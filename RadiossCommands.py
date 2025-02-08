import FreeCAD
import FreeCADGui
import FemGui
import Part
import os
from PySide2.QtWidgets import QFileDialog
import ObjectsFem

class RadiossMaterial:
    def GetResources(self):
        return {'Pixmap': 'fem-material',
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
        return {'Pixmap': 'fem-constraint',
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
        return {'Pixmap': 'fem-force',
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
        return {'Pixmap': 'fem-set',
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
        return {'Pixmap': 'fem-analysis',
                'MenuText': 'Create Radioss Analysis',
                'ToolTip': 'Creates a new Radioss analysis'}

    def Activated(self):
        import FemGui
        analysis = FemGui.getActiveAnalysis()
        if not analysis:
            analysis = FemGui.createAnalysis('Analysis')
        
        # Add specific Radioss properties/settings here
        analysis.addProperty("App::PropertyString", "SolverType", "Radioss", "Solver Type").SolverType = "OpenRadioss"
        
        FreeCAD.ActiveDocument.recompute()
        return

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

class RadiossAnalysisProperties:
    def GetResources(self):
        return {'Pixmap': 'fem-solver',
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
        return {'Pixmap': 'fem-export',
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
        return {'Pixmap': 'fem-import',
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
            analysis = FemGui.createAnalysis('Analysis')

        self.import_radioss(analysis, filename[0])

    def import_radioss(self, analysis, filepath):
        """RadiossファイルをインポートしてFreeCADオブジェクトを作成"""
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()

            # パーサーの初期化
            parser = RadiossFileParser()
            model_data = parser.parse(lines)

            # FreeCADオブジェクトの作成
            self.create_freecad_objects(analysis, model_data)

            FreeCAD.ActiveDocument.recompute()
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"Import error: {str(e)}\n")

    def create_freecad_objects(self, analysis, model_data):
        """パースしたデータからFreeCADオブジェクトを作成"""
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
        for constraint in model_data.constraints:
            const_obj = self.create_constraint(constraint)
            analysis.addObject(const_obj)

        # 荷重の作成
        for load in model_data.loads:
            load_obj = self.create_load(load)
            analysis.addObject(load_obj)
        
        # 剛体の作成
        for rbody_data in model_data.rbodies:
            rbody_obj = self.create_rbody(rbody_data)
            analysis.addObject(rbody_obj)
        
        # 接触の作成
        for contact_data in model_data.contacts:
            contact_obj = self.create_contact(contact_data)
            analysis.addObject(contact_obj)
    
    def create_rbody(self, rbody_data):
        """剛体オブジェクトの作成"""
        rbody = FreeCAD.ActiveDocument.addObject("App::FeaturePython", f"RBody_{rbody_data['name']}")
        rbody.addProperty("App::PropertyString", "RBodyName", "RBody", "Name of rigid body")
        rbody.RBodyName = rbody_data['name']
        
        # 質量と重心の設定
        rbody.addProperty("App::PropertyFloat", "Mass", "RBody", "Mass of rigid body")
        rbody.Mass = rbody_data['mass']
        rbody.addProperty("App::PropertyVector", "CenterOfMass", "RBody", "Center of mass")
        rbody.CenterOfMass = FreeCAD.Vector(*rbody_data['com'])
        
        # 慣性モーメントの設定
        rbody.addProperty("App::PropertyVector", "Inertia", "RBody", "Inertia tensor")
        rbody.Inertia = FreeCAD.Vector(*rbody_data['inertia'])
        
        # 拘束条件の設定
        for prop in ['FixX', 'FixY', 'FixZ', 'FixRX', 'FixRY', 'FixRZ']:
            rbody.addProperty("App::PropertyBool", prop, "Motion", f"Fix {prop[-1]} {'rotation' if 'R' in prop else 'translation'}")
            setattr(rbody, prop, False)
        
        # 拘束条件の適用
        for constraint in rbody_data['constraints']:
            if constraint == 1: rbody.FixX = True
            elif constraint == 2: rbody.FixY = True
            elif constraint == 3: rbody.FixZ = True
            elif constraint == 4: rbody.FixRX = True
            elif constraint == 5: rbody.FixRY = True
            elif constraint == 6: rbody.FixRZ = True
        
        return rbody

    def create_contact(self, contact_data):
        """接触オブジェクトの作成"""
        contact = FreeCAD.ActiveDocument.addObject("App::FeaturePython", f"Contact_{contact_data['name']}")
        contact.addProperty("App::PropertyString", "ContactName", "Contact", "Name of contact")
        contact.ContactName = contact_data['name']
        
        # 接触タイプの設定
        contact.addProperty("App::PropertyEnumeration", "ContactType", "Contact", "Type of contact")
        contact.ContactType = ["TYPE7", "TYPE11", "TYPE19"]
        contact.ContactType = contact_data['type']
        
        # 接触パラメータの設定
        contact.addProperty("App::PropertyFloat", "Gap", "Parameters", "Initial gap")
        contact.Gap = contact_data['gap']
        contact.addProperty("App::PropertyFloat", "Friction", "Parameters", "Friction coefficient")
        contact.Friction = contact_data['friction']
        contact.addProperty("App::PropertyFloat", "Stiffness", "Parameters", "Contact stiffness")
        contact.Stiffness = contact_data['stiffness']
        contact.addProperty("App::PropertyFloat", "Damping", "Parameters", "Contact damping")
        contact.Damping = contact_data['damping']
        
        return contact
    
    def create_mesh(self, nodes, elements):
        """ノードと要素からFEMメッシュを作成"""
        mesh_obj = ObjectsFem.makeMeshGmsh(FreeCAD.ActiveDocument, 'FEMMesh')
        mesh = mesh_obj.FemMesh

        # ノードの追加
        for node_id, coords in nodes.items():
            mesh.addNode(coords[0], coords[1], coords[2], node_id)

        # 要素の追加
        for elem_id, (elem_type, node_ids) in elements.items():
            if elem_type == "SHELL":
                mesh.addFace4Node(*node_ids, elem_id)
            elif elem_type == "SOLID":
                mesh.addVolume8Node(*node_ids, elem_id)

        return mesh_obj

    def create_material(self, mat_data):
        """材料プロパティオブジェクトを作成"""
        material = ObjectsFem.makeMaterialSolid(FreeCAD.ActiveDocument, mat_data['name'])
        material.Material = {
            'Name': mat_data['name'],
            'YoungsModulus': f"{mat_data['young']:f} MPa",
            'PoissonRatio': str(mat_data['poisson']),
            'Density': f"{mat_data['density']:f} kg/m^3",
            'RadiossType': mat_data['law']
        }
        return material

    def create_set(self, set_data):
        """セットオブジェクトを作成"""
        set_obj = FreeCAD.ActiveDocument.addObject("App::FeaturePython", f"Set_{set_data['name']}")
        set_obj.addProperty("App::PropertyString", "SetType", "Radioss", "Type of set")
        set_obj.SetType = set_data['type']
        set_obj.addProperty("App::PropertyIntegerList", "Members", "Radioss", "Set members")
        set_obj.Members = set_data['members']
        return set_obj

    def create_constraint(self, const_data):
        """境界条件オブジェクトを作成"""
        if const_data['type'] == 'FIXED':
            constraint = ObjectsFem.makeConstraintFixed(FreeCAD.ActiveDocument, const_data['name'])
            # 参照セットの設定
            if 'references' in const_data:
                constraint.References = const_data['references']
        return constraint

    def create_load(self, load_data):
        """荷重オブジェクトを作成"""
        if load_data['type'] == 'FORCE':
            force = ObjectsFem.makeConstraintForce(FreeCAD.ActiveDocument, load_data['name'])
            force.Force = load_data['magnitude']
            force.DirectionVector = load_data['direction']
            if 'references' in load_data:
                force.References = load_data['references']
        return force

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None

class RadiossFileParser:
    """Radiossファイルのパーサー"""
    def __init__(self):
        self.nodes = {}
        self.elements = {}
        self.materials = []
        self.sets = []
        self.constraints = []
        self.loads = []
        self.current_section = None
        self.rbodies = []
        self.contacts = []

    def parse(self, lines):
        """Radiossファイルを解析"""
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            if line.startswith('/'):
                self.current_section = line
                continue

            self.parse_section(line)

        return self

    def parse_section(self, line):
        """セクションごとの解析"""
        if self.current_section == '/NODE':
            self.parse_node(line)
        elif self.current_section.startswith('/ELEMENT'):
            self.parse_element(line)
        elif self.current_section.startswith('/MAT'):
            self.parse_material(line)
        elif self.current_section.startswith('/SET'):
            self.parse_set(line)
        elif self.current_section.startswith('/BOUND'):
            self.parse_constraint(line)
        elif self.current_section.startswith('/LOAD'):
            self.parse_load(line)
        elif self.current_section.startswith('/RBODY'):
            self.parse_rbody(line)
        elif self.current_section.startswith('/INTER'):
            self.parse_contact(line)
    
    
    def parse_rbody(self, line):
        """剛体データの解析"""
        if not line.startswith('/'):
            data = line.split()
            rbody = {
                'name': data[0],
                'node_set': int(data[1]),
                'mass': float(data[2]) if len(data) > 2 else 0.0,
                'com': [float(data[3]), float(data[4]), float(data[5])] if len(data) > 5 else [0,0,0],
                'inertia': [float(x) for x in data[6:9]] if len(data) > 8 else [0,0,0],
                'constraints': [int(x) for x in data[9:]] if len(data) > 9 else []
            }
            self.rbodies.append(rbody)

    def parse_contact(self, line):
        """接触データの解析"""
        if not line.startswith('/'):
            data = line.split()
            contact = {
                'name': data[0],
                'type': self.current_section.split('/')[2],
                'slave_set': int(data[1]),
                'master_set': int(data[2]),
                'gap': float(data[3]) if len(data) > 3 else 0.0,
                'friction': float(data[4]) if len(data) > 4 else 0.0,
                'stiffness': float(data[5]) if len(data) > 5 else 0.0,
                'damping': float(data[6]) if len(data) > 6 else 0.0
            }
            self.contacts.append(contact)
    
    def parse_node(self, line):
        """ノードデータの解析"""
        data = line.split()
        node_id = int(data[0])
        coords = [float(x) for x in data[1:4]]
        self.nodes[node_id] = coords

    def parse_element(self, line):
        """要素データの解析"""
        data = line.split()
        elem_id = int(data[0])
        elem_type = self.current_section.split('/')[2]
        node_ids = [int(x) for x in data[2:]]
        self.elements[elem_id] = (elem_type, node_ids)

    def parse_material(self, line):
        """材料データの解析"""
        if not line.startswith('/'):
            data = line.split()
            mat = {
                'name': data[0],
                'law': self.current_section.split('/')[2],
                'young': float(data[1]),
                'poisson': float(data[2]),
                'density': float(data[3])
            }
            self.materials.append(mat)

    def parse_set(self, line):
        """セットデータの解析"""
        if not line.startswith('/'):
            data = line.split()
            set_data = {
                'name': data[0],
                'type': self.current_section.split('/')[2],
                'members': [int(x) for x in data[1:]]
            }
            self.sets.append(set_data)

    def parse_constraint(self, line):
        """境界条件データの解析"""
        if not line.startswith('/'):
            data = line.split()
            const = {
                'name': data[0],
                'type': self.current_section.split('/')[2],
                'nodes': [int(x) for x in data[1:]]
            }
            self.constraints.append(const)

    def parse_load(self, line):
        """荷重データの解析"""
        if not line.startswith('/'):
            data = line.split()
            load = {
                'name': data[0],
                'type': self.current_section.split('/')[2],
                'magnitude': float(data[1]),
                'direction': FreeCAD.Vector(
                    float(data[2]),
                    float(data[3]),
                    float(data[4])
                )
            }
            self.loads.append(load)


class RadiossRigidBody:
    def GetResources(self):
        return {'Pixmap': 'fem-rigid-body',
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
        return {'Pixmap': 'fem-contact',
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
