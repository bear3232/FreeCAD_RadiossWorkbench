import FreeCADGui


class RadiossWorkbench(Workbench):
    def __init__(self):
        self.__class__.MenuText = "Radioss"
        self.__class__.ToolTip = "これはカスタムワークベンチの例です"

    def Initialize(self):
        import RadiossCommands
        # Add commands to FreeCAD
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

    def Activated(self):
        return

    def Deactivated(self):
        return

    def GetClassName(self):
        return "Gui::PythonWorkbench"

FreeCADGui.addWorkbench(RadiossWorkbench())
