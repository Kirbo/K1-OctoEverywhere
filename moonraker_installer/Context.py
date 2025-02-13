import os
import json

from .Logging import Logger

# This class holds the context of the installer, meaning all of the target vars and paths
# that this instance is using.
# There is a generation system, where generation defines what data is required by when.
# Generation 1 - Must always exist, from the start.
# Generation 2 - Must exist after the discovery phase.
# Generation 3 - Must exist after the configure phase.
class Context:

    def __init__(self) -> None:

        # Generation 1 - This is the repo root of OctoEverywhere. This is common for all instances.
        self.RepoRootFolder = None

        # Generation 1 -This is the path to the PY virtual env for OctoEverywhere. This is common for all instances.
        self.VirtualEnvPath = None

        # Generation 1 -This is the user name of the user who launched the install script.
        # Useful because this module is running as a sudo user.
        self.UserName = None

        # Generation 1 -This is the user home path of the user who launched the install script.
        # Useful because this module is running as a sudo user.
        self.UserHomePath = None

        # Generation 1 - A string containing all of the args the install script was launched with.
        self.CmdLineArgs = None

        # Generation 1  -Parsed from the command line args, if debug should be enabled.
        self.Debug = False

        # Generation 1 - Parsed from the command line args, if we should show help.
        self.ShowHelp = False

        # Generation 1 - Parsed from the command line args, if we should skip sudo actions for debugging.
        self.SkipSudoActions = False

        # Generation 1 - Parsed from the command line args, if set, we shouldn't auto select the moonraker instance.
        self.DisableAutoMoonrakerInstanceSelection = False

        # Generation 2 - This is the full file path to the moonraker config.
        self.MoonrakerConfigFilePath = None

        # Generation 2 -This is the file name of the moonraker service we are targeting.
        self.MoonrakerServiceFileName = None

        # Generation 3 - This it the path to the printer data root folder.
        self.PrinterDataFolder = None

        # Generation 3 - This it the path to the printer data config folder.
        self.PrinterDataConfigFolder = None

        # Generation 3 - This it the path to the printer data logs folder.
        self.PrinterDataLogsFolder = None

        # Generation 3 - This is the name of this OctoEverywhere instance's service.
        self.ServiceName = None

        # Generation 3 - The full file path and file name of this instance's service file.
        self.ServiceFilePath = None

        # Generation 3 - The path to where the local storage will be put for this instance.
        self.LocalFileStorageFolder = None

        # Generation 4 - If the instance config file existed before we created the service, this will hold the printer id.
        self.ExistingPrinterId = None


    @staticmethod
    def LoadFromArgString(argString:str):
        Logger.Debug("Found config: "+argString)
        argObj = json.loads(argString)
        context = Context()
        context.RepoRootFolder = argObj["OE_REPO_DIR"]
        context.VirtualEnvPath = argObj["OE_ENV"]
        context.UserName = argObj["USERNAME"]
        context.UserHomePath = argObj["USER_HOME"]
        context.CmdLineArgs = argObj["CMD_LINE_ARGS"]
        return context


    def Validate(self, generation = 1) -> None:
        self._ValidatePathAndExists(self.RepoRootFolder, "Required Env Var OE_REPO_DIR was not found; make sure to run the install.sh script to begin the installation process")
        self._ValidatePathAndExists(self.VirtualEnvPath, "Required Env Var OE_ENV was not found; make sure to run the install.sh script to begin the installation process")
        self._ValidatePathAndExists(self.UserHomePath, "Required Env Var USER_HOME was not found; make sure to run the install.sh script to begin the installation process")
        self._ValidateString(self.UserName, "Required Env Var USERNAME was not found; make sure to run the install.sh script to begin the installation process")
        self._ValidateString(self.UserName, "Required Env Var USERNAME was not found; make sure to run the install.sh script to begin the installation process")
        # Can be an empty string, but not None.
        if self.CmdLineArgs is None:
            raise Exception("Required Env Var CMD_LINE_ARGS was not found; make sure to run the install.sh script to begin the installation process.")

        # Since these exist, clean them up.
        self.RepoRootFolder = self.RepoRootFolder.strip()
        self.VirtualEnvPath = self.VirtualEnvPath.strip()
        self.UserName = self.UserName.strip()
        self.UserHomePath = self.UserHomePath.strip()
        self.CmdLineArgs = self.CmdLineArgs.strip()

        if generation >= 2:
            self._ValidatePathAndExists(self.MoonrakerConfigFilePath, "Required config var Moonraker Config File Path was not found")
            self._ValidateString(self.MoonrakerServiceFileName, "Required config var Moonraker Service File Name was not found")

            # All systems assume this file ends in .service, so make sure it does.
            self.MoonrakerConfigFilePath = self.MoonrakerConfigFilePath.strip()
            self.MoonrakerServiceFileName = self.MoonrakerServiceFileName.strip()
            if self.MoonrakerServiceFileName.lower().endswith(".service") is False:
                self.MoonrakerServiceFileName += ".service"

        if generation >= 3:
            self._ValidatePathAndExists(self.PrinterDataFolder, "Required config var Printer Data Folder was not found")
            self._ValidatePathAndExists(self.PrinterDataConfigFolder, "Required config var Printer Data Config Folder was not found")
            self._ValidatePathAndExists(self.PrinterDataLogsFolder, "Required config var Printer Data Logs Folder was not found")
            self._ValidatePathAndExists(self.PrinterDataLogsFolder, "Required config var Printer Data Logs Folder was not found")
            self._ValidatePathAndExists(self.LocalFileStorageFolder, "Required config var local storage folder was not found")
            # This path wont exist on the first install, because it won't be created until the end of the install.
            self._ValidateString(self.ServiceFilePath, "Required config var service file path was not found")
            self._ValidateString(self.ServiceName, "Required config var service name was not found")

        if generation >= 4:
            # The printer ID can be None, this means it didn't exist before we installed the service.
            pass


    def ParseCmdLineArgs(self):
        # Handle the original cmdline args.
        # The format is <moonraker config file path> <moonraker service file path> -other -args
        # Where both file paths are optional, but if only one is given, it's assumed to be the config file path.
        args = self.CmdLineArgs.split(' ')
        for a in args:
            # Ensure there's a string and it's not empty.
            # If no args are passed, there will be one empty string after the split.
            if isinstance(a, str) is False or len(a) == 0:
                continue

            # Handle and flags passed.
            if a[0] == '-':
                rawArg = a[1:]
                if rawArg.lower() == "debug":
                    # Enable debug printing.
                    self.Debug = True
                    Logger.EnableDebugLogging()
                elif rawArg.lower() == "help" or rawArg.lower() == "usage" or rawArg.lower() == "h":
                    self.ShowHelp = True
                elif rawArg.lower() == "skipsudoactions":
                    Logger.Warn("Skipping sudo actions. ! This will not result in a valid install! ")
                    self.SkipSudoActions = True
                elif rawArg.lower() == "noatuoselect":
                    Logger.Info("Disabling Moonraker instance auto selection.")
                    self.DisableAutoMoonrakerInstanceSelection = True
                else:
                    raise Exception("Unknown argument found. Use install.sh -help for options.")

            # If there's a raw string, assume its a config path or service file name.
            else:
                if self.MoonrakerConfigFilePath is None:
                    self.MoonrakerConfigFilePath = a
                    Logger.Debug("Moonraker config file path found as argument:"+self.MoonrakerConfigFilePath)
                elif self.MoonrakerServiceFileName is None:
                    self.MoonrakerServiceFileName = a
                    Logger.Debug("Moonraker service file name found as argument:"+self.MoonrakerServiceFileName)
                else:
                    raise Exception("Unknown argument found. Use install.sh -help for options.")


    def _ValidatePathAndExists(self, path:str, error:str):
        if path is None or os.path.exists(path) is False:
            raise Exception(error)


    def _ValidateString(self, s:str, error:str):
        if s is None or isinstance(s, str) is False or len(s) == 0:
            raise Exception(error)
