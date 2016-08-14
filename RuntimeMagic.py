import os
import sys
import unittest

CONFIG_FILE = "./wt.conf"
MAP_FILE = "uid_file.map"
PROCESS = '"/vagrant/a.out"'
FUNCTION  = '"a"'
RETURN = 1

STAP_EXECUTE = "stap -v -g"
STAP_SPACE   = " "
STAP_SCRIPT_COLLECT = "collect_script.stp"
STAP_SCRIPT_TRIGGER = "trigger_script.stp"

TEST_UID = "0x4004c8 0x4004e1 0x40050b 0x40051b"

###### Unit Test ######

class TestClassStackidVector(unittest.TestCase):
    def test_popstackid(self):
        vec = ["abcd\n", "efgh\n", "ijkl\n"]
        f = open("testmap", "w")
        for line in vec:
            f.write(line)
        f.close()

        stack_vec = StackidVector("testmap")
        self.assertTrue(stack_vec.IsValid)
        self.assertEqual(stack_vec.PopStackid(), "abcd")

###### SRC Code ######

# Vector
class StackidVector:
    def __init__(self, filename):
        self.v = []
        self.f = None
        self.name = filename

        if not os.path.exists(self.name):
            self.state = False
        else:
            self.state =  True
            l = self.LoadStackid()
            if l == 0:
                self.state = False
            else:
                print self.v

    def IsValid(self):
        return self.state
  
    def PopStackid(self):
        popid = self.v[0] 
        self.v.remove(self.v[0])
        self.SaveStackid()
        return popid

    def LoadStackid(self):
        self.f = open(self.name, "r")
        for line in self.f:
            self.v.append(line.strip(os.linesep))
        self.f.close()
        return len(self.v)

    def SaveStackid(self):
        self.f = open(self.name, "w") 
        for line in self.v:
            self.f.write(line)
        self.f.close()

# Template
class StapTemplete(object):
    f = None
    name = None
    def __init__(self, script_name):
        self.name = script_name
        if self.CheckScript():
            os.remove(self.name)
          
        self.f = open(self.name, "w")

    def CloseScript(self):
        self.f.close()

    def CheckScript(self):
        return os.path.exists(self.name)

    def GenerateGetUserStack(self):
        script = []
        script.append('%{' + os.linesep)
        script.append('#include <linux/string.h>' + os.linesep)
        script.append('%}' + os.linesep)
        script.append(os.linesep)
        script.append('function GetUserStack:string(stack:string)' + os.linesep)
        script.append('%{' + os.linesep)
        script.append('    char *uid = (char *)STAP_ARG_stack;' + os.linesep)
        script.append('    int len = strlen(uid) - 14;' + os.linesep)
        script.append('    snprintf(STAP_RETVALUE, len, "%s", uid);' + os.linesep)
        script.append('%}' + os.linesep)
        script.append(os.linesep)
        for s in script:
            self.f.write(s)

    def GenerateScript(self):
        pass

class FunctionTriggerScript(StapTemplete):
    def __init__(self, uid):
        super(FunctionTriggerScript, self).__init__(STAP_SCRIPT_TRIGGER)
        self.uid = uid

    def GenerateGlobalEnter(self):
        script = "global enter" + os.linesep
        self.f.write(script)

    def GenerateProbe(self, process, function):
        script = "probe process(" + process + ").function(" + function + ")" + os.linesep 
        self.f.write(script)

    def GenerateProbeReturn(self, process, function):
        script = "probe process(" + process + ").function(" + function + ").return" + os.linesep
        self.f.write(script)

    def GenerateBody(self):
        script = []      
        script.append("{" + os.linesep)
        script.append("    enter = 0" + os.linesep)
        script.append("    stack = ubacktrace()" + os.linesep)
        script.append("    stack = GetUserStack(stack)" + os.linesep)
        script.append("    if (stack == \"" + self.uid + "\")" + os.linesep)
        script.append("    {" + os.linesep)
        script.append("        enter = 1" + os.linesep)
        script.append("        println(\"oooooooooooooooo\")" + os.linesep)
        script.append("    }" + os.linesep)
        script.append("}" + os.linesep)
        script.append(os.linesep)

        for s in script:
            self.f.write(s)

    def GenerateReturnBody(self):
        script = []
        script.append("{" + os.linesep)
        script.append("    if (enter == 1)" + os.linesep)
        script.append("    {" + os.linesep)
        script.append("        $return=" + str(RETURN) + os.linesep)
        script.append("        exit()" + os.linesep)
        script.append("    }" + os.linesep)
        script.append("}" + os.linesep)
        script.append(os.linesep)
        for s in script:
            self.f.write(s)

    def GenerateScript(self):
        self.GenerateGetUserStack()
        self.GenerateGlobalEnter()
        self.GenerateProbe(PROCESS, FUNCTION)
        self.GenerateBody()
        self.GenerateProbeReturn(PROCESS, FUNCTION)
        self.GenerateReturnBody()
        self.CloseScript()

class CollectScript(StapTemplete):
    def __init__(self):
        super(CollectScript, self).__init__(STAP_SCRIPT_COLLECT)

    def GenerateScript(self):
        self.GenerateGetUserStack()
        self.GenerateProbe(PROCESS, FUNCTION)
        self.GenerateBody()
        self.CloseScript()

    def GenerateProbe(self, process, function):
        script = "probe process("+ process + ").function(" + function + ")" + os.linesep
        self.f.write(script)
    
    def GenerateBody(self):
        script = []  
        script.append("{" + os.linesep)
        script.append("    stack = ubacktrace()" + os.linesep)
        script.append("    println(GetUserStack(stack))" + os.linesep)
        script.append("}" + os.linesep)
        script.append(os.linesep)
        for s in script:
            self.f.write(s)

# Executor
class StapExecutor:
    command = STAP_EXECUTE
    def __init__(self):
        self.command = ""
    def execute(self):
        print self.command
        os.system(self.command)

class TriggerStapExecutor(StapExecutor):
    def __init__(self, script):
        self.command = self.command + STAP_SPACE + script

class CollectStapExecutor(StapExecutor):
    def __init__(self, scrpit):
        self.command = self.command + STAP_SPACE + scrpit + STAP_SPACE + "-o " + MAP_FILE

# Command
class CollectCommand():
    def run(self):
        stap = CollectStapExecutor(STAP_SCRIPT_COLLECT)
        stap.execute()

class FunctionTriggerCommand():
    def run(self):
        stap = TriggerStapExecutor(STAP_SCRIPT_TRIGGER)
        stap.execute()

# Factory
def StapScriptFactory(subcommand,vector=None):
    script = None
    if subcommand == "collect":
        script = CollectScript() 
    if subcommand == "trigger":
        script = FunctionTriggerScript(vector.PopStackid())

    return script

def SubCommandFactory(subcommand):
    command = None

    if subcommand == "collect":
        script = StapScriptFactory(subcommand)
        script.GenerateScript()
        command = CollectCommand()

    if subcommand == "trigger":
        uid_vec =  StackidVector(MAP_FILE)
        if uid_vec.IsValid() == False:
             return "mapfile_error"

        script = StapScriptFactory(subcommand, uid_vec)
        script.GenerateScript()
        command = FunctionTriggerCommand()
   
    return command

# Main
def main():

    if not os.path.exists(CONFIG_FILE):
        print "without config file!"
        return
   
    if len(sys.argv) != 2 :
        print "argument error!" 
        return 

    subcommand = sys.argv[1]
    if subcommand != "collect" and subcommand != "trigger":
        print "subcommand error!"
        return  

    command = SubCommandFactory(subcommand)
    if command == None:
        print "command error!"
        return
    elif command == "mapfile_error":
        print "without mapfile or empty mapfile"
        return 
     
    command.run()

if __name__ == '__main__': main()
#if __name__ == '__main__': unittest.main()
