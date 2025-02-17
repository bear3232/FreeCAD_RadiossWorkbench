import FreeCAD
import FreeCADGui
import FemGui
import Part
import os
from PySide2.QtWidgets import QFileDialog
import ObjectsFem
from types import SimpleNamespace
import Fem  # FemMeshのために追加

# from femtools.femutils import FemMesh の代わりに以下を使用
FemMesh = Fem.FemMesh  # FemMeshクラスの取得

class RadiossMaterial:
    def GetResources(self):
        return {'Pixmap': '',
                'MenuText': 'Add Radioss Material',
                'ToolTip': 'Add a material for Radioss analysis'}

    def Activated(self):
        analysis = FemGui.getActiveAnalysis()
        if analysis:
            material = ObjectsFem.makeMaterialSolid(FreeCAD.ActiveDocument, "RadiossMaterial")
            material.Category = 'Solid'
            material.Material = {
                'Name': 'Steel',
                'YoungsModulus': '210000 MPa',
                'PoissonRatio': '0.3',
                'Density': '7800 kg/m^3',
                'YieldStrength': '250 MPa',
                'UltimateStrength': '400 MPa',
                'RadiossType': 'LAW2',  # Elastic-plastic material law
                'HardeningParam': '0.2'
            }
            analysis.addObject(material)

    def IsActive(self):
        return FemGui.getActiveAnalysis() is not None

class RadiossConstraint:
    def GetResources(self):
        return {'Pixmap': '',
                'MenuText': 'Add Radioss Constraint',
                'ToolTip': 'Add a constraint for Radioss analysis'}

    def Activated(self):
        analysis = FemGui.getActiveAnalysis()
        if analysis:
            constraint = ObjectsFem.makeConstraintFixed(FreeCAD.ActiveDocument, "RadiossConstraint")
            analysis.addObject(constraint)

    def IsActive(self):
        return FemGui.getActiveAnalysis() is not None

class RadiossLoad:
    def GetResources(self):
        return {'Pixmap': '',
                'MenuText': 'Add Radioss Load',
                'ToolTip': 'Add a load for Radioss analysis'}

    def Activated(self):
        analysis = FemGui.getActiveAnalysis()
        if analysis:
            force = ObjectsFem.makeConstraintForce(FreeCAD.ActiveDocument, "RadiossForce")
            analysis.addObject(force)

    def IsActive(self):
        return FemGui.getActiveAnalysis() is not None

class RadiossSet:
    def GetResources(self):
        return {'Pixmap': '',
                'MenuText': 'Create Radioss Set',
                'ToolTip': 'Create a node or element set for Radioss'}

    def Activated(self):
        analysis = FemGui.getActiveAnalysis()
        if analysis:
            set_obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "RadiossSet")
            set_obj.addProperty("App::PropertyString", "SetType", "Radioss", "Type of set").SetType = "NODE"
            set_obj.addProperty("App::PropertyLinkList", "References", "Radioss", "Set references")
            analysis.addObject(set_obj)

    def IsActive(self):
        return FemGui.getActiveAnalysis() is not None

class RadiossAnalysis:
    def GetResources(self):
        return {'Pixmap': '',
                'MenuText': 'Create Radioss Analysis',
                'ToolTip': 'Creates a new Radioss analysis'}

    def Activated(self):
        import ObjectsFem
        
        # アクティブな解析を取得
        analysis = FemGui.getActiveAnalysis()
        
        # 解析オブジェクトが存在しない場合は新規作成
        if not analysis:
            analysis = ObjectsFem.makeAnalysis(FreeCAD.ActiveDocument, 'Analysis')
            FreeCAD.ActiveDocument.recompute()
        
        # Radioss固有のプロパティを追加
        if not hasattr(analysis, "SolverType"):
            analysis.addProperty("App::PropertyString", "SolverType", "Radioss", "Solver Type")
        analysis.SolverType = "OpenRadioss"
        
        FreeCAD.ActiveDocument.recompute()
        return

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

class RadiossAnalysisProperties:
    def GetResources(self):
        return {'Pixmap': '',
                'MenuText': 'Radioss Analysis Properties',
                'ToolTip': 'Set Radioss analysis properties'}

    def Activated(self):
        analysis = FemGui.getActiveAnalysis()
        if analysis:
            properties = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "RadiossProperties")
            
            # 時間設定
            properties.addProperty("App::PropertyFloat", "TerminationTime", "Time", 
                                 "Analysis termination time").TerminationTime = 1.0
            properties.addProperty("App::PropertyFloat", "TimeStep", "Time", 
                                 "Initial time step").TimeStep = 1.0e-6
            properties.addProperty("App::PropertyFloat", "DTScale", "Time", 
                                 "Time step scale factor").DTScale = 0.9
            
            # 出力設定
            properties.addProperty("App::PropertyFloat", "PrintTime", "Output", 
                                 "Time interval for output").PrintTime = 0.001
            properties.addProperty("App::PropertyBool", "StressOutput", "Output", 
                                 "Output stress results").StressOutput = True
            properties.addProperty("App::PropertyBool", "StrainOutput", "Output", 
                                 "Output strain results").StrainOutput = True
            properties.addProperty("App::PropertyBool", "DisplacementOutput", "Output", 
                                 "Output displacement results").DisplacementOutput = True
            
            # 解析設定
            properties.addProperty("App::PropertyEnumeration", "TimeIntegration", "Solver", 
                                 "Time integration method")
            properties.TimeIntegration = ["Central_Difference"]
            properties.addProperty("App::PropertyFloat", "Damping", "Solver", 
                                 "Global damping coefficient").Damping = 0.0
            
            analysis.addObject(properties)

    def IsActive(self):
        return FemGui.getActiveAnalysis() is not None


class RadiossExport:
    def GetResources(self):
        return {'Pixmap': '',
                'MenuText': 'Export to Radioss',
                'ToolTip': 'Export the model to Radioss format'}

    def Activated(self):
        analysis = FemGui.getActiveAnalysis()
        if not analysis:
            FreeCAD.Console.PrintError("No active analysis found!\n")
            return

        # Starterファイルの保存
        starter_filename = QFileDialog.getSaveFileName(None, "Export Radioss Starter Deck",
                                                     None, "Radioss Starter (*.rad)")
        if not starter_filename[0]:
            return

        # Engineファイルの名前を自動生成（拡張子をD00に変更）
        engine_filename = os.path.splitext(starter_filename[0])[0] + ".D00"

        self.export_radioss_starter(analysis, starter_filename[0])
        self.export_radioss_engine(analysis, engine_filename)

    def export_radioss_starter(self, analysis, filepath):
        with open(filepath, 'w') as f:
            # Write header
            f.write("/RADIOSS STARTER\n")
            f.write("# Generated by FreeCAD Radioss Workbench\n\n")

            # Get mesh
            mesh = None
            for member in analysis.Group:
                if member.isDerivedFrom("Fem::FemMeshObject"):
                    mesh = member
                    break

            if not mesh:
                FreeCAD.Console.PrintError("No mesh found in analysis!\n")
                return

            # Write node definitions
            f.write("/NODE\n")
            for i, node in enumerate(mesh.FemMesh.Nodes, 1):
                pos = mesh.FemMesh.Nodes[node]
                f.write(f"{i:8d} {pos[0]:12.5E} {pos[1]:12.5E} {pos[2]:12.5E}\n")

            # Write element definitions
            f.write("\n/ELEMENT/SHELL\n")
            for i, elem in enumerate(mesh.FemMesh.Volumes, 1):
                nodes = mesh.FemMesh.getElementNodes(elem)
                node_str = " ".join([f"{n:8d}" for n in nodes])
                f.write(f"{i:8d} {1:8d} {node_str}\n")
            
            # 剛体の出力
            self.write_rbodies(f, analysis)
            
            # 接触の出力
            self.write_contacts(f, analysis)
            
            # Write sets
            self.write_sets(f, analysis)

            # Write materials
            self.write_materials(f, analysis)

            # Write constraints
            self.write_constraints(f, analysis)

            # Write loads
            self.write_loads(f, analysis)

            f.write("\n/END\n")
    
    
    def write_rbodies(self, f, analysis):
        """剛体データの出力"""
        f.write("\n# Rigid Bodies\n")
        for obj in analysis.Group:
            if hasattr(obj, 'RBodyName'):
                f.write("/RBODY/LAGMUL\n")  # LAGMULタイプの剛体として出力
                f.write(f"{obj.RBodyName}")
                
                # ノードセット参照
                if obj.NodeSet:
                    f.write(f" {obj.NodeSet.Name}")
                
                # 質量と重心
                f.write(f" {obj.Mass:12.5E}")
                com = obj.CenterOfMass
                f.write(f" {com.x:12.5E} {com.y:12.5E} {com.z:12.5E}")
                
                # 慣性モーメント
                inertia = obj.Inertia
                f.write(f" {inertia.x:12.5E} {inertia.y:12.5E} {inertia.z:12.5E}")
                
                # 拘束条件
                constraints = []
                if obj.FixX: constraints.append(1)
                if obj.FixY: constraints.append(2)
                if obj.FixZ: constraints.append(3)
                if obj.FixRX: constraints.append(4)
                if obj.FixRY: constraints.append(5)
                if obj.FixRZ: constraints.append(6)
                if constraints:
                    f.write(" " + " ".join(map(str, constraints)))
                
                f.write("\n")

    def write_contacts(self, f, analysis):
        """接触データの出力"""
        f.write("\n# Contacts\n")
        for obj in analysis.Group:
            if hasattr(obj, 'ContactName'):
                f.write(f"/INTER/{obj.ContactType}\n")
                f.write(f"{obj.ContactName}")
                
                # スレーブ/マスターセット参照
                if obj.SlaveSet:
                    f.write(f" {obj.SlaveSet.Name}")
                if obj.MasterSet:
                    f.write(f" {obj.MasterSet.Name}")
                
                # 接触パラメータ
                f.write(f" {obj.Gap:12.5E}")
                f.write(f" {obj.Friction:12.5E}")
                f.write(f" {obj.Stiffness:12.5E}")
                f.write(f" {obj.Damping:12.5E}")
                
                f.write("\n")
    
    
    def write_sets(self, f, analysis):
        f.write("\n# Sets\n")
        for member in analysis.Group:
            if hasattr(member, "SetType"):
                f.write(f"/SET/{member.SetType}\n")
                f.write(f"{member.Name}\n")
                # Get node or element IDs from references
                ids = self.get_ids_from_references(member.References)
                # Write IDs in groups of 8
                for i in range(0, len(ids), 8):
                    f.write(" ".join(f"{id:8d}" for id in ids[i:i+8]) + "\n")

    def write_materials(self, f, analysis):
        f.write("\n# Materials\n")
        for member in analysis.Group:
            if member.isDerivedFrom("App::MaterialObjectPython"):
                mat = member.Material
                f.write(f"/MAT/{mat.get('RadiossType', 'LAW2')}\n")
                f.write(f"{member.Name}\n")
                # Write material properties
                f.write(f"{float(mat['YoungsModulus'].split()[0]):12.5E} ")  # E
                f.write(f"{float(mat['PoissonRatio']):12.5E} ")              # nu
                f.write(f"{float(mat['Density'].split()[0]):12.5E} ")        # rho
                f.write(f"{float(mat['YieldStrength'].split()[0]):12.5E} ")  # yield stress
                f.write(f"{float(mat.get('HardeningParam', '0.0')):12.5E}\n")  # hardening parameter

    def write_constraints(self, f, analysis):
        f.write("\n# Boundary Conditions\n")
        for member in analysis.Group:
            if member.isDerivedFrom("Fem::ConstraintFixed"):
                f.write("/BOUND/FIXED\n")
                f.write(f"{member.Name}\n")
                # Get node set for the constraint
                nodes = self.get_constrained_nodes(member)
                for i in range(0, len(nodes), 8):
                    f.write(" ".join(f"{node:8d}" for node in nodes[i:i+8]) + "\n")

    def write_loads(self, f, analysis):
        f.write("\n# Loads\n")
        for member in analysis.Group:
            if member.isDerivedFrom("Fem::ConstraintForce"):
                f.write("/LOAD/FORCE\n")
                f.write(f"{member.Name}\n")
                # Write force magnitude and direction
                f.write(f"{member.Force:12.5E} ")
                f.write(f"{member.DirectionVector.x:12.5E} ")
                f.write(f"{member.DirectionVector.y:12.5E} ")
                f.write(f"{member.DirectionVector.z:12.5E}\n")
                # Get nodes where force is applied
                nodes = self.get_force_nodes(member)
                for i in range(0, len(nodes), 8):
                    f.write(" ".join(f"{node:8d}" for node in nodes[i:i+8]) + "\n")

    def get_ids_from_references(self, references):
        # Helper method to get IDs from references
        ids = []
        for ref in references:
            # Add logic to extract IDs based on reference type
            pass
        return ids

    def get_constrained_nodes(self, constraint):
        # Helper method to get nodes for constraint
        nodes = []
        # Add logic to get constrained nodes
        return nodes

    def get_force_nodes(self, force):
        # Helper method to get nodes for force
        nodes = []
        # Add logic to get force application nodes
        return nodes

    def IsActive(self):
        return FemGui.getActiveAnalysis() is not None
    
    def export_radioss_engine(self, analysis, filepath):
        # 解析プロパティの取得
        properties = None
        for obj in analysis.Group:
            if obj.Name.startswith("RadiossProperties"):
                properties = obj
                break

        if not properties:
            FreeCAD.Console.PrintWarning("No analysis properties found. Using defaults.\n")
            return

        with open(filepath, 'w') as f:
            # ヘッダー
            f.write("/RADIOSS ENGINE\n")
            f.write("# Generated by FreeCAD Radioss Workbench\n\n")

            # 時間制御
            f.write("/RUN/1\n")
            f.write(f"{properties.TerminationTime:12.5E}\n")
            
            # タイムステップ制御
            f.write("/DT\n")
            f.write(f"{properties.TimeStep:12.5E} {properties.DTScale:12.5E}\n")
            
            # 出力制御
            f.write("/PRINT/-1\n")
            f.write(f"{properties.PrintTime:12.5E}\n")
            
            # アニメーション出力設定
            f.write("/ANIM/DT\n")
            f.write(f"{properties.PrintTime:12.5E}\n")
            
            # 出力変数の指定
            if properties.StressOutput:
                f.write("/ANIM/TENS/STRESS\n")
            if properties.StrainOutput:
                f.write("/ANIM/TENS/STRAIN\n")
            if properties.DisplacementOutput:
                f.write("/ANIM/TENS/DISPLACEMENT\n")
            
            # ダンピング設定
            if properties.Damping > 0:
                f.write("/DAMPING/GLOBAL\n")
                f.write(f"{properties.Damping:12.5E}\n")
            
            # タイムインテグレーション設定
            if properties.TimeIntegration == "Central_Difference":
                f.write("/DEF_CENT/ON\n")
            
            # 終了
            f.write("/END\n")
    
    def get_analysis_properties(self, analysis):
        """解析プロパティのデフォルト値を取得"""
        return {
            'TerminationTime': 1.0,
            'TimeStep': 1.0e-6,
            'DTScale': 0.9,
            'PrintTime': 0.001,
            'StressOutput': True,
            'StrainOutput': True,
            'DisplacementOutput': True,
            'TimeIntegration': 'Central_Difference',
            'Damping': 0.0
        }



class RadiossImport:
    def GetResources(self):
        return {'Pixmap': '',
                'MenuText': 'Import Radioss Model',
                'ToolTip': 'Import a Radioss model file'}

    def Activated(self):
        # ファイル選択ダイアログを表示
        filename = QFileDialog.getOpenFileName(None, "Import Radioss Model",
                                             None, "Radioss Files (*.rad)")
        if not filename[0]:
            return

        # 新しい解析オブジェクトを作成
        analysis = FemGui.getActiveAnalysis()
        if not analysis:
            analysis = ObjectsFem.makeAnalysis(FreeCAD.ActiveDocument, 'Analysis')
            FreeCAD.ActiveDocument.recompute()

        self.import_radioss(analysis, filename[0])

    def import_radioss(self, analysis, filepath):
        """RadiossファイルをインポートしてFreeCADオブジェクトを作成"""
        FreeCAD.Console.PrintLog(f"Importing Radioss file: {filepath}\n")
        try:
            print(f"Reading file: {filepath}\n")
            with open(filepath, 'r') as f:
                lines = f.readlines()

            print(f"Parsing {len(lines)} lines\n")
            # パーサーの初期化
            parser = RadiossFileParser()
            model_data = parser.parse(lines)

            # パース結果の確認
            print(f"Parsed data summary:\n")
            print(f"Nodes: {len(model_data.nodes)}\n")
            print(f"Elements: {len(model_data.elements)}\n")
            print(f"Materials: {len(model_data.materials)}\n")

            # FreeCADオブジェクトの作成
            self.create_freecad_objects(analysis, model_data)

            FreeCAD.ActiveDocument.recompute()
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"Import error: {str(e)}\n")

    def create_freecad_objects(self, analysis, model_data):
        """パースしたデータからFreeCADオブジェクトを作成"""
        print(f"Creating FreeCAD objects\n")
        FreeCAD.Console.PrintLog(f"Creating FreeCAD objects\n")
        try:
            # メッシュの作成
            if model_data.nodes and model_data.elements:
                mesh = self.create_mesh(model_data.nodes, model_data.elements)
                analysis.addObject(mesh)

            # 材料の作成
            for mat in model_data.materials:
                material = self.create_material(mat)
                analysis.addObject(material)

            # セットの作成
            for set_data in model_data.sets:
                set_obj = self.create_set(set_data)
                analysis.addObject(set_obj)

            # 境界条件の作成
            for const in model_data.constraints:
                constraint = self.create_constraint(const)
                analysis.addObject(constraint)

            # 荷重の作成
            for load in model_data.loads:
                load_obj = self.create_load(load)
                analysis.addObject(load_obj)

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error creating objects: {str(e)}\n")

    def create_mesh(self, nodes, elements):
        """メッシュオブジェクトの作成"""
        try:
            # メッシュオブジェクトの作成
            mesh_obj = ObjectsFem.makeMeshGmsh(FreeCAD.ActiveDocument, 'FEMMesh')
            
            # 新しいFemMeshオブジェクトの作成
            mesh = FemMesh()

            # ノードの追加
            FreeCAD.Console.PrintLog(f"Adding {len(nodes)} nodes to mesh\n")
            for node_id, coords in nodes.items():
                try:
                    mesh.addNode(coords[0], coords[1], coords[2], node_id)
                except Exception as e:
                    FreeCAD.Console.PrintError(f"Error adding node {node_id}: {str(e)}\n")

            # 要素の追加
            shellcount = 0
            FreeCAD.Console.PrintLog(f"Adding {len(elements)} elements to mesh\n")
            for elem_id, elem in elements.items():
                try:
                    if elem.type == 'SHELL' and len(elem.nodes) >= 4:
                        mesh.addFace(elem.nodes, elem_id)
                        shellcount += 1
                    elif elem.type == 'SH3N' and len(elem.nodes) >= 3:
                        # 3節点シェル要素
                        mesh.addFace(elem.nodes, elem_id)
                        shellcount += 1
                    elif elem.type == "SOLID":
                        if len(elem.nodes) == 8:
                            # mesh.addVolume(elem.nodes, elem_id)
                            pass
                        elif len(elem.nodes) == 4:
                            # 4節点四面体要素
                            # mesh.addVolume(elem.nodes, elem_id)
                            pass
                except Exception as e:
                    FreeCAD.Console.PrintError(f"Error adding element {elem_id}: {str(e)}\n")
            print(shellcount)
            # メッシュをオブジェクトに設定
            mesh_obj.FemMesh = mesh

            # シェル要素の厚さを設定
            if hasattr(self, 'properties'):
                for elem_id, elem in elements.items():
                    if elem.type == "SHELL" and hasattr(elem, 'property'):
                        try:
                            thickness = self.get_shell_thickness(elem.property)
                            if thickness:
                                # 要素グループを作成して厚さを設定
                                group_name = f"ShellThickness_{thickness}"
                                if not hasattr(mesh_obj, group_name):
                                    mesh_obj.addProperty("App::PropertyFloat", group_name, "Shell Thickness", 
                                                       "Shell thickness for element group")
                                    setattr(mesh_obj, group_name, thickness)
                                # 要素をグループに追加
                                if not hasattr(mesh_obj, f"{group_name}_elements"):
                                    mesh_obj.addProperty("App::PropertyIntegerList", f"{group_name}_elements", 
                                                       "Shell Thickness", "Elements in thickness group")
                                getattr(mesh_obj, f"{group_name}_elements").append(elem_id)
                        except Exception as e:
                            FreeCAD.Console.PrintError(f"Error setting shell thickness for element {elem_id}: {str(e)}\n")

            # メッシュの表示を更新
            mesh_obj.ViewObject.DisplayMode = "Faces & Wireframe"
            mesh_obj.ViewObject.BackfaceCulling = False
            FreeCAD.ActiveDocument.recompute()
                
            FreeCAD.Console.PrintLog("Mesh creation completed\n")
            return mesh_obj

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error creating mesh: {str(e)}\n")
            return None

    def get_shell_thickness(self, prop_id):
        """シェル要素の厚さを取得"""
        for prop in self.properties:
            if prop.id == prop_id and prop.type == "SHELL":
                return prop.thickness
        return None

    def create_material(self, mat_data):
        """材料プロパティオブジェクトを作成"""
        material = ObjectsFem.makeMaterialSolid(FreeCAD.ActiveDocument, mat_data.name)
        material.Material = {
            'Name': mat_data.name,
            'YoungsModulus': f"{mat_data.E} MPa",
            'PoissonRatio': str(mat_data.nu),
            'Density': f"{mat_data.rho} kg/m^3",
            'RadiossType': mat_data.type
        }

        # オプションのプロパティ
        if hasattr(mat_data, 'yield_stress'):
            material.Material['YieldStrength'] = f"{mat_data.yield_stress} MPa"
        if hasattr(mat_data, 'hardening'):
            material.Material['HardeningParam'] = str(mat_data.hardening)

        return material

    def create_set(self, set_data):
        """セットオブジェクトを作成"""
        set_obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", f"Set_{set_data.name}")
        set_obj.addProperty("App::PropertyString", "SetType", "Radioss", "Type of set")
        set_obj.SetType = set_data.type
        set_obj.addProperty("App::PropertyIntegerList", "Members", "Radioss", "Set members")
        set_obj.Members = set_data.members
        return set_obj

    def create_constraint(self, const_data):
        """境界条件オブジェクトを作成"""
        if const_data.type == 'FIXED':
            constraint = ObjectsFem.makeConstraintFixed(FreeCAD.ActiveDocument, f"Constraint_{const_data.id}")
            # 参照ノードの設定
            if hasattr(const_data, 'nodes'):
                constraint.References = [(FreeCAD.ActiveDocument.FEMMesh, 'Node' + str(n)) for n in const_data.nodes]
        return constraint

    def create_load(self, load_data):
        """荷重オブジェクトを作成"""
        force = ObjectsFem.makeConstraintForce(FreeCAD.ActiveDocument, f"Force_{load_data.id}")
        force.Force = load_data.magnitude
        force.DirectionVector = FreeCAD.Vector(*load_data.direction)
        # 参照ノードの設定
        if hasattr(load_data, 'nodes'):
            force.References = [(FreeCAD.ActiveDocument.FEMMesh, 'Node' + str(n)) for n in load_data.nodes]
        return force

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

class RadiossFileParser:
    def __init__(self):
        self.nodes = {}
        self.elements = {}
        self.materials = []
        self.sets = []
        self.constraints = []
        self.loads = []
        self.properties = []  # プロパティリストを追加
        self.current_section = None
        self.current_subsection = None

    def parse(self, lines):
        """Radiossファイルを解析"""
        try:
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                if line.startswith('/'):
                    self.current_section = line
                    FreeCAD.Console.PrintLog(f"Found section: {line}\n")
                    continue

                try:
                    self.parse_section(line)
                except Exception as e:
                    FreeCAD.Console.PrintWarning(f"Warning: Failed to parse line: {line}\nError: {str(e)}\n")

        except Exception as e:
            FreeCAD.Console.PrintError(f"Parse error: {str(e)}\n")
            
        # パース結果のサマリーを出力
        shellcount = 0
        for elem_id, elem in self.elements.items():
            if elem.type == "SHELL":
                shellcount += 1
        print(shellcount)
        FreeCAD.Console.PrintLog(f"Parse completed:\n")
        FreeCAD.Console.PrintLog(f"  Nodes: {len(self.nodes)}\n")
        FreeCAD.Console.PrintLog(f"  Elements: {len(self.elements)}\n")
        FreeCAD.Console.PrintLog(f"  Materials: {len(self.materials)}\n")
        FreeCAD.Console.PrintLog(f"  Properties: {len(self.properties)}\n")
        FreeCAD.Console.PrintLog(f"  Sets: {len(self.sets)}\n")
        FreeCAD.Console.PrintLog(f"  Constraints: {len(self.constraints)}\n")
        FreeCAD.Console.PrintLog(f"  Loads: {len(self.loads)}\n")
            
        return self

    def parse_section(self, line):
        """セクションごとの解析"""
        if not self.current_section:
            return

        # セクション名を正規化
        section = self.current_section.upper()
        
        FreeCAD.Console.PrintLog(f"Parsing section: {section}, line: {line}\n")

        if section.startswith('/NODE'):
            self.parse_node(line)
        elif section.startswith('/SHELL'):
            prop_id = self.current_section.split('/')[2]
            self.parse_element(line, "SHELL", prop_id)
        elif section.startswith('/SH3N'):
            prop_id = self.current_section.split('/')[2]
            self.parse_element(line, "SH3N", prop_id)
        elif section.startswith('/BRICK'):
            prop_id = self.current_section.split('/')[2]
            self.parse_element(line, "SOLID", prop_id)
        elif section.startswith('/PART/'):
            prop_id = self.current_section.split('/')[2]
            mat_id = 1
            self.parse_property(line, "SHELL", prop_id, mat_id)
        elif section.startswith('/PROP/SHELL'):
            prop_id = self.current_section.split('/')[3]
            mat_id = 1
            self.parse_property(line, "SHELL", prop_id, mat_id)
        elif section.startswith('/PROP/SOLID'):
            prop_id = self.current_section.split('/')[3]
            mat_id = 1
            self.parse_property(line, "SOLID", prop_id, mat_id)
        elif section.startswith('/MAT/'):
            self.parse_material(line)
        elif section.startswith('/SET/'):
            self.parse_set(line)
        elif section.startswith('/BOUNDARY'):
            self.parse_constraint(line)
        elif section.startswith('/LOAD'):
            self.parse_load(line)

    def parse_property(self, line, prop_type, prop_id, mat_id):
        """プロパティデータの解析"""
        data = self.clean_data(line)
        if len(data) >= 3:  # ID + 材料ID + 厚さ/その他のパラメータ
            try:
                # prop_id = int(data[0])
                # mat_id = int(data[1])
                
                prop = SimpleNamespace(
                    id=prop_id,
                    type=prop_type,
                    material=mat_id
                )

                if prop_type == "SHELL":
                    prop.thickness = 1.0
                    # prop.thickness = float(data[2])
                elif prop_type == "SOLID":
                    # SOLIDプロパティの追加パラメータがあれば設定
                    pass

                self.properties.append(prop)
                FreeCAD.Console.PrintLog(f"Parsed property {prop_id}: {prop_type}\n")
            except (ValueError, IndexError) as e:
                FreeCAD.Console.PrintWarning(f"Warning: Invalid property data: {line}\nError: {str(e)}\n")

    def parse_element(self, line, elem_type, prop_id):
        """要素データの解析"""
        data = self.clean_data(line)
        if len(data) >= 3:  # ID + ノード
            try:
                elem_id = int(data[0])
                # prop_id = int(data[1])
                nodes = []
                if elem_type == 'SHELL':
                    for node_str in data[1:5]:
                        if node_str:
                            nodes.append(int(node_str))
                elif elem_type == 'SH3N':
                    for node_str in data[1:4]:
                        if node_str:
                            nodes.append(int(node_str))
                elif elem_type == 'SOLID':
                    for node_str in data[1:]:
                        if node_str:
                            nodes.append(int(node_str))
                if nodes:
                    self.elements[elem_id] = SimpleNamespace(
                        id=elem_id,
                        property=prop_id,
                        nodes=nodes,
                        type=elem_type
                    )
                    FreeCAD.Console.PrintLog(f"Parsed element {elem_id}: {elem_type}, nodes: {nodes}\n")
            except (ValueError, IndexError) as e:
                FreeCAD.Console.PrintWarning(f"Warning: Invalid element data: {line}\nError: {str(e)}\n")

    def clean_data(self, line):
        """データ行をクリーンアップして分割"""
        # カンマまたは空白で分割
        if ',' in line:
            data = [x.strip() for x in line.split(',')]
        else:
            data = line.split()
        
        # 空の要素を削除
        return [x for x in data if x]

    def parse_node(self, line):
        """ノードデータの解析"""
        data = self.clean_data(line)
        if len(data) >= 4:  # ID + 3座標
            try:
                node_id = int(data[0])
                coords = [float(x) for x in data[1:4]]
                self.nodes[node_id] = coords
                FreeCAD.Console.PrintLog(f"Parsed node {node_id}: {coords}\n")
            except (ValueError, IndexError) as e:
                FreeCAD.Console.PrintWarning(f"Warning: Invalid node data: {line}\nError: {str(e)}\n")

    def parse_material(self, line):
        """材料データの解析"""
        data = self.clean_data(line)
        if len(data) >= 5:  # 最低限必要なデータ数
            try:
                mat = SimpleNamespace(
                    name=data[0],
                    type=data[1],
                    E=float(data[2]),
                    nu=float(data[3]),
                    rho=float(data[4])
                )
                
                # オプションのプロパティ
                if len(data) > 5:
                    mat.yield_stress = float(data[5])
                if len(data) > 6:
                    mat.hardening = float(data[6])
                    
                self.materials.append(mat)
            except (ValueError, IndexError):
                FreeCAD.Console.PrintWarning(f"Warning: Invalid material data: {line}\n")

    def parse_set(self, line):
        """セットデータの解析"""
        data = self.clean_data(line)
        if len(data) >= 2:  # 名前 + 要素
            try:
                set_data = SimpleNamespace(
                    name=data[0],
                    type=self.current_section.split('/')[1],
                    members=[int(x) for x in data[1:] if x]
                )
                self.sets.append(set_data)
            except (ValueError, IndexError):
                FreeCAD.Console.PrintWarning(f"Warning: Invalid set data: {line}\n")

    def parse_constraint(self, line):
        """境界条件データの解析"""
        data = self.clean_data(line)
        if len(data) >= 2:  # ID + ノード
            try:
                nodes = [int(x) for x in data[1:] if x]
                if nodes:
                    self.constraints.append(SimpleNamespace(
                        id=int(data[0]),
                        nodes=nodes,
                        type="FIXED"
                    ))
            except (ValueError, IndexError):
                FreeCAD.Console.PrintWarning(f"Warning: Invalid constraint data: {line}\n")

    def parse_load(self, line):
        """荷重データの解析"""
        data = self.clean_data(line)
        if len(data) >= 5:  # ID + 大きさ + 方向(x,y,z)
            try:
                self.loads.append(SimpleNamespace(
                    id=int(data[0]),
                    magnitude=float(data[1]),
                    direction=[float(x) for x in data[2:5]]
                ))
            except (ValueError, IndexError):
                FreeCAD.Console.PrintWarning(f"Warning: Invalid load data: {line}\n")


class RadiossRigidBody:
    def GetResources(self):
        return {'Pixmap': '',
                'MenuText': 'Add Rigid Body',
                'ToolTip': 'Create a rigid body definition'}

    def Activated(self):
        analysis = FemGui.getActiveAnalysis()
        if analysis:
            rbody = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "RadiossRBody")
            
            # 剛体の基本プロパティ
            rbody.addProperty("App::PropertyString", "RBodyName", "RBody", 
                            "Name of rigid body").RBodyName = "RBody1"
            rbody.addProperty("App::PropertyLink", "NodeSet", "RBody", 
                            "Node set for rigid body")
            rbody.addProperty("App::PropertyVector", "CenterOfMass", "RBody", 
                            "Center of mass").CenterOfMass = FreeCAD.Vector(0,0,0)
            rbody.addProperty("App::PropertyFloat", "Mass", "RBody", 
                            "Mass of rigid body").Mass = 1.0
            rbody.addProperty("App::PropertyVector", "Inertia", "RBody", 
                            "Inertia tensor").Inertia = FreeCAD.Vector(1,1,1)
            
            # 運動制御
            rbody.addProperty("App::PropertyBool", "FixX", "Motion", 
                            "Fix X translation").FixX = False
            rbody.addProperty("App::PropertyBool", "FixY", "Motion", 
                            "Fix Y translation").FixY = False
            rbody.addProperty("App::PropertyBool", "FixZ", "Motion", 
                            "Fix Z translation").FixZ = False
            rbody.addProperty("App::PropertyBool", "FixRX", "Motion", 
                            "Fix X rotation").FixRX = False
            rbody.addProperty("App::PropertyBool", "FixRY", "Motion", 
                            "Fix Y rotation").FixRY = False
            rbody.addProperty("App::PropertyBool", "FixRZ", "Motion", 
                            "Fix Z rotation").FixRZ = False
            
            analysis.addObject(rbody)

    def IsActive(self):
        return FemGui.getActiveAnalysis() is not None

class RadiossContact:
    def GetResources(self):
        return {'Pixmap': '',
                'MenuText': 'Add Contact',
                'ToolTip': 'Create a contact definition'}

    def Activated(self):
        analysis = FemGui.getActiveAnalysis()
        if analysis:
            contact = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "RadiossContact")
            
            # 接触の基本プロパティ
            contact.addProperty("App::PropertyString", "ContactName", "Contact", 
                              "Name of contact").ContactName = "Contact1"
            contact.addProperty("App::PropertyEnumeration", "ContactType", "Contact", 
                              "Type of contact")
            contact.ContactType = ["TYPE7", "TYPE11", "TYPE19"]
            contact.addProperty("App::PropertyLink", "SlaveSet", "Contact", 
                              "Slave node/segment set")
            contact.addProperty("App::PropertyLink", "MasterSet", "Contact", 
                              "Master node/segment set")
            
            # 接触パラメータ
            contact.addProperty("App::PropertyFloat", "Gap", "Parameters", 
                              "Initial gap").Gap = 0.0
            contact.addProperty("App::PropertyFloat", "Friction", "Parameters", 
                              "Friction coefficient").Friction = 0.0
            contact.addProperty("App::PropertyFloat", "Stiffness", "Parameters", 
                              "Contact stiffness").Stiffness = 0.0
            contact.addProperty("App::PropertyFloat", "Damping", "Parameters", 
                              "Contact damping").Damping = 0.0
            
            analysis.addObject(contact)

    def IsActive(self):
        return FemGui.getActiveAnalysis() is not None

class LsDynaImport:
    def GetResources(self):
        return {'Pixmap': '',
                'MenuText': 'Import from LS-DYNA',
                'ToolTip': 'Import an LS-DYNA model file'}

    def Activated(self):
        # ファイル選択ダイアログを表示
        filename = QFileDialog.getOpenFileName(None, "Import LS-DYNA Model",
                                             None, "LS-DYNA Files (*.k *.key)")
        if not filename[0]:
            return

        # 新しい解析オブジェクトを作成
        analysis = FemGui.getActiveAnalysis()
        if not analysis:
            analysis = ObjectsFem.makeAnalysis(FreeCAD.ActiveDocument, 'Analysis')
            FreeCAD.ActiveDocument.recompute()

        self.import_lsdyna(analysis, filename[0])

    def import_lsdyna(self, analysis, filepath):
        """LS-DYNAファイルをインポートしてRadiossモデルに変換"""
        try:
            parser = LsDynaParser()
            model_data = parser.parse_file(filepath)
            self.convert_to_radioss(analysis, model_data)
            FreeCAD.ActiveDocument.recompute()
        except Exception as e:
            FreeCAD.Console.PrintError(f"Import error: {str(e)}\n")

    def convert_to_radioss(self, analysis, dyna_data):
        """LS-DYNAデータをRadiossオブジェクトに変換"""
        # メッシュの変換
        if dyna_data.nodes and dyna_data.elements:
            mesh = self.create_mesh(dyna_data.nodes, dyna_data.elements)
            analysis.addObject(mesh)

        # 材料の変換
        for mat in dyna_data.materials:
            radioss_mat = self.convert_material(mat)
            analysis.addObject(radioss_mat)

        # 境界条件の変換
        for spc in dyna_data.boundary_conditions:
            radioss_constraint = self.convert_constraint(spc)
            analysis.addObject(radioss_constraint)

        # 荷重の変換
        for load in dyna_data.loads:
            radioss_load = self.convert_load(load)
            analysis.addObject(radioss_load)

        # 接触の変換
        for contact in dyna_data.contacts:
            radioss_contact = self.convert_contact(contact)
            analysis.addObject(radioss_contact)

    def create_mesh(self, nodes, elements):
        """LS-DYNAメッシュデータからFEMメッシュを作成"""
        mesh_obj = ObjectsFem.makeMeshGmsh(FreeCAD.ActiveDocument, 'FEMMesh')
        mesh = mesh_obj.FemMesh

        # ノードの追加
        for node_id, coords in nodes.items():
            mesh.addNode(coords[0], coords[1], coords[2], node_id)

        # 要素の追加
        for elem_id, elem_data in elements.items():
            if elem_data.type == "SHELL":
                mesh.addFace4Node(*elem_data.nodes, elem_id)
            elif elem_data.type == "SOLID":
                mesh.addVolume8Node(*elem_data.nodes, elem_id)

        return mesh_obj

    def create_material(self, dyna_mat):
        """LS-DYNA材料をRadioss材料に変換"""
        mat = ObjectsFem.makeMaterialSolid(FreeCAD.ActiveDocument, f"RadiossMaterial_{dyna_mat.id}")
        
        # 材料タイプの変換マッピング
        material_mapping = {
            'MAT_ELASTIC': 'LAW2',
            'MAT_PLASTIC_KINEMATIC': 'LAW36',
            'MAT_PIECEWISE_LINEAR_PLASTICITY': 'LAW36'
        }

        # 基本的な材料プロパティの設定
        mat.Material = {
            'Name': dyna_mat.name,
            'YoungsModulus': f"{dyna_mat.E} MPa",
            'PoissonRatio': str(dyna_mat.nu),
            'Density': f"{dyna_mat.rho} kg/m^3",
            'RadiossType': material_mapping.get(dyna_mat.type, 'LAW2')
        }

        # 降伏応力と硬化パラメータの設定
        if hasattr(dyna_mat, 'yield_stress'):
            mat.Material['YieldStrength'] = f"{dyna_mat.yield_stress} MPa"
        if hasattr(dyna_mat, 'tangent_modulus'):
            mat.Material['HardeningParam'] = str(dyna_mat.tangent_modulus)

        return mat

    def convert_constraint(self, dyna_spc):
        """LS-DYNA拘束をRadioss拘束に変換"""
        constraint = ObjectsFem.makeConstraintFixed(FreeCAD.ActiveDocument, f"RadiossConstraint_{dyna_spc.id}")
        
        # 拘束ノードの設定
        if hasattr(dyna_spc, 'nodes'):
            constraint.References = [(FreeCAD.ActiveDocument.FEMMesh, 'Node' + str(n)) for n in dyna_spc.nodes]
        
        return constraint

    def convert_load(self, dyna_load):
        """LS-DYNA荷重をRadioss荷重に変換"""
        load = ObjectsFem.makeConstraintForce(FreeCAD.ActiveDocument, f"RadiossLoad_{dyna_load.id}")
        
        # 荷重値と方向の設定
        if hasattr(dyna_load, 'magnitude'):
            load.Force = dyna_load.magnitude
        if hasattr(dyna_load, 'direction'):
            load.DirectionVector = FreeCAD.Vector(*dyna_load.direction)
        
        # 荷重適用ノードの設定
        if hasattr(dyna_load, 'nodes'):
            load.References = [(FreeCAD.ActiveDocument.FEMMesh, 'Node' + str(n)) for n in dyna_load.nodes]
        
        return load

    def convert_contact(self, dyna_contact):
        """LS-DYNA接触をRadioss接触に変換"""
        contact = FreeCAD.ActiveDocument.addObject("App::FeaturePython", f"RadiossContact_{dyna_contact.id}")
        
        # 接触タイプの変換マッピング
        contact_mapping = {
            'AUTOMATIC_SURFACE_TO_SURFACE': 'TYPE7',
            'TIED_SURFACE_TO_SURFACE': 'TYPE2',
            'NODES_TO_SURFACE': 'TYPE11'
        }
        
        # 基本プロパティの設定
        contact.addProperty("App::PropertyString", "ContactName", "Contact", "Name of contact")
        contact.ContactName = f"Contact_{dyna_contact.id}"
        
        contact.addProperty("App::PropertyEnumeration", "ContactType", "Contact", "Type of contact")
        contact.ContactType = ["TYPE7", "TYPE11", "TYPE19"]
        contact.ContactType = contact_mapping.get(dyna_contact.type, 'TYPE7')
        
        # 接触パラメータの設定
        if hasattr(dyna_contact, 'static_friction'):
            contact.addProperty("App::PropertyFloat", "Friction", "Parameters", "Friction coefficient")
            contact.Friction = dyna_contact.static_friction
        
        return contact

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None


class LsDynaParser:
    """LS-DYNAキーワードファイルのパーサー"""
    def __init__(self):
        self.nodes = {}
        self.elements = {}
        self.materials = []
        self.boundary_conditions = []
        self.loads = []
        self.contacts = []
        self.current_keyword = None

    def parse_file(self, filepath):
        """LS-DYNAファイルを解析"""
        with open(filepath, 'r') as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()
            if not line or line.startswith('$'):  # コメントをスキップ
                continue

            if line.startswith('*'):
                self.current_keyword = line[1:].strip().upper()
                continue

            try:
                self.parse_keyword_data(line)
            except Exception as e:
                FreeCAD.Console.PrintWarning(f"Warning: Failed to parse line: {line}\nError: {str(e)}\n")

        return self

    def clean_data(self, line):
        """データ行をクリーンアップして分割"""
        # カンマまたは空白で分割
        if ',' in line:
            data = [x.strip() for x in line.split(',')]
        else:
            data = line.split()
        
        # 空の要素を削除
        return [x for x in data if x]

    def parse_keyword_data(self, line):
        """キーワードに基づいてデータを解析"""
        if not self.current_keyword:
            return

        if self.current_keyword.startswith('NODE'):
            self.parse_node(line)
        elif self.current_keyword.startswith('ELEMENT'):
            self.parse_element(line)
        elif self.current_keyword.startswith('MAT'):
            self.parse_material(line)
        elif self.current_keyword.startswith('BOUNDARY_SPC'):
            self.parse_boundary(line)
        elif self.current_keyword.startswith('LOAD'):
            self.parse_load(line)
        elif self.current_keyword.startswith('CONTACT'):
            self.parse_contact(line)

    def parse_node(self, line):
        """ノードデータの解析"""
        data = self.clean_data(line)
        if len(data) >= 4:  # ID + 3座標
            try:
                node_id = int(data[0])
                coords = [float(x) for x in data[1:4]]
                self.nodes[node_id] = coords
            except (ValueError, IndexError):
                FreeCAD.Console.PrintWarning(f"Warning: Invalid node data: {line}\n")

    def parse_element(self, line):
        """要素データの解析"""
        data = self.clean_data(line)
        if len(data) >= 3:  # ID + 材料ID + ノード
            try:
                elem_id = int(data[0])
                elem_type = self.current_keyword.split('_')[1] if '_' in self.current_keyword else 'SOLID'
                nodes = []
                for node_str in data[2:]:
                    if node_str:
                        nodes.append(int(node_str))
                if nodes:
                    self.elements[elem_id] = SimpleNamespace(type=elem_type, nodes=nodes)
            except (ValueError, IndexError):
                FreeCAD.Console.PrintWarning(f"Warning: Invalid element data: {line}\n")

    def parse_material(self, line):
        """材料データの解析"""
        data = self.clean_data(line)
        if len(data) >= 4:  # ID + E + nu + rho
            try:
                mat_id = int(data[0])
                material = SimpleNamespace(
                    id=mat_id,
                    type=self.current_keyword,
                    name=f"Material_{mat_id}",
                    E=float(data[1]),
                    nu=float(data[2]),
                    rho=float(data[3])
                )
                
                # オプションのプロパティ
                if len(data) > 4:
                    material.yield_stress = float(data[4])
                if len(data) > 5:
                    material.tangent_modulus = float(data[5])
                    
                self.materials.append(material)
            except (ValueError, IndexError):
                FreeCAD.Console.PrintWarning(f"Warning: Invalid material data: {line}\n")

    def parse_boundary(self, line):
        """境界条件データの解析"""
        data = self.clean_data(line)
        if len(data) >= 2:  # ID + ノード
            try:
                spc_id = int(data[0])
                nodes = [int(x) for x in data[1:] if x]
                if nodes:
                    self.boundary_conditions.append(SimpleNamespace(id=spc_id, nodes=nodes))
            except (ValueError, IndexError):
                FreeCAD.Console.PrintWarning(f"Warning: Invalid boundary condition data: {line}\n")

    def parse_load(self, line):
        """荷重データの解析"""
        data = self.clean_data(line)
        if len(data) >= 6:  # ID + ノード + 大きさ + 方向(x,y,z)
            try:
                load_id = int(data[0])
                nodes = [int(data[1])]
                magnitude = float(data[2])
                direction = [float(x) for x in data[3:6]]
                self.loads.append(SimpleNamespace(
                    id=load_id,
                    nodes=nodes,
                    magnitude=magnitude,
                    direction=direction
                ))
            except (ValueError, IndexError):
                FreeCAD.Console.PrintWarning(f"Warning: Invalid load data: {line}\n")

    def parse_contact(self, line):
        """接触データの解析"""
        data = self.clean_data(line)
        if len(data) >= 1:  # 最低限ID
            try:
                contact_id = int(data[0])
                contact_type = self.current_keyword.split('_', 1)[1] if '_' in self.current_keyword else 'AUTOMATIC'
                
                contact = SimpleNamespace(
                    id=contact_id,
                    type=contact_type
                )
                
                if len(data) > 1:
                    contact.static_friction = float(data[1])
                    
                self.contacts.append(contact)
            except (ValueError, IndexError):
                FreeCAD.Console.PrintWarning(f"Warning: Invalid contact data: {line}\n")
