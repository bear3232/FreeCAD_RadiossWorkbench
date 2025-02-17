import FreeCADGui

class RadiossWorkbench(Workbench):
    def __init__(self):
        self.__class__.MenuText = "Radioss"
        self.__class__.ToolTip = "これはカスタムワークベンチの例です"
        
        # ツールバーのアイコンリストを定義
        self.__class__.Icon = """
            /* XPM */
            static char * radioss_xpm[] = {
            "16 16 3 1",
            " 	c None",
            ".	c #000000",
            "+	c #FFFFFF",
            "                ",
            "       ..       ",
            "      .++.      ",
            "     .++++.     ",
            "    .++++++.    ",
            "   .++++++++.   ",
            "  .++++++++++.  ",
            " .++++++++++++. ",
            " .++++++++++++. ",
            "  .++++++++++.  ",
            "   .++++++++.   ",
            "    .++++++.    ",
            "     .++++.     ",
            "      .++.      ",
            "       ..       ",
            "                "};
            """

    def Initialize(self):
        import RadiossCommands

        # コマンドリストの定義
        self.analysis_commands = [
            'Radioss_Analysis',
            'Radioss_AnalysisProperties'
        ]
        
        self.modeling_commands = [
            'Radioss_Material',
            'Radioss_Constraint',
            'Radioss_Load',
            'Radioss_Set',
            'Radioss_RigidBody',
            'Radioss_Contact'
        ]
        
        self.io_commands = [
            'Radioss_Import',
            'Radioss_Export',
            'LsDyna_Import'
        ]

        # コマンドの追加
        FreeCADGui.addCommand('Radioss_Import', RadiossCommands.RadiossImport())
        FreeCADGui.addCommand('Radioss_Analysis', RadiossCommands.RadiossAnalysis())
        FreeCADGui.addCommand('Radioss_Material', RadiossCommands.RadiossMaterial())
        FreeCADGui.addCommand('Radioss_Constraint', RadiossCommands.RadiossConstraint())
        FreeCADGui.addCommand('Radioss_Load', RadiossCommands.RadiossLoad())
        FreeCADGui.addCommand('Radioss_Set', RadiossCommands.RadiossSet())
        FreeCADGui.addCommand('Radioss_RigidBody', RadiossCommands.RadiossRigidBody())
        FreeCADGui.addCommand('Radioss_Contact', RadiossCommands.RadiossContact())
        FreeCADGui.addCommand('Radioss_Export', RadiossCommands.RadiossExport())
        FreeCADGui.addCommand('Radioss_AnalysisProperties', RadiossCommands.RadiossAnalysisProperties())
        FreeCADGui.addCommand('LsDyna_Import', RadiossCommands.LsDynaImport())

        # ツールバーの作成
        self.appendToolbar('Radioss Analysis', self.analysis_commands)
        self.appendToolbar('Radioss Modeling', self.modeling_commands)
        self.appendToolbar('Radioss I/O', self.io_commands)
        
        # メニューの作成
        self.appendMenu('Radioss Analysis', self.analysis_commands)
        self.appendMenu('Radioss Modeling', self.modeling_commands)
        self.appendMenu('Radioss I/O', self.io_commands)

    def Activated(self):
        return

    def Deactivated(self):
        return

    def GetClassName(self):
        return "Gui::PythonWorkbench"

FreeCADGui.addWorkbench(RadiossWorkbench())
