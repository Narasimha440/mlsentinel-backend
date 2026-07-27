from sqlalchemy.orm import Session
from app.models.workspace import Workspace
from app.models.project import Project
from app.models.ml_model import MLModel


class HierarchyService:

    @staticmethod
    def get_or_create_workspace(db: Session, firebase_uid: str) -> Workspace:
        workspace = db.query(Workspace).filter(Workspace.owner_firebase_uid == firebase_uid).first()
        if not workspace:
            workspace = Workspace(name=f"{firebase_uid}'s Workspace", owner_firebase_uid=firebase_uid)
            db.add(workspace)
            db.commit()
            db.refresh(workspace)
        return workspace

    @staticmethod
    def get_or_create_project(db: Session, workspace_id: int, project_name: str) -> Project:
        project = db.query(Project).filter(
            Project.workspace_id == workspace_id, Project.name == project_name
        ).first()
        if not project:
            project = Project(workspace_id=workspace_id, name=project_name)
            db.add(project)
            db.commit()
            db.refresh(project)
        return project

    @staticmethod
    def get_or_create_model(db: Session, project_id: int, model_name: str) -> MLModel:
        model = db.query(MLModel).filter(
            MLModel.project_id == project_id, MLModel.name == model_name
        ).first()
        if not model:
            model = MLModel(project_id=project_id, name=model_name)
            db.add(model)
            db.commit()
            db.refresh(model)
        return model

    @staticmethod
    def resolve_model_id(db: Session, firebase_uid: str, project_name: str, model_name: str) -> int:
        workspace = HierarchyService.get_or_create_workspace(db, firebase_uid)
        project = HierarchyService.get_or_create_project(db, workspace.id, project_name)
        model = HierarchyService.get_or_create_model(db, project.id, model_name)
        return model.id

    def find_model_id_for_owner(db: Session, firebase_uid: str, project_name: str, model_name: str) -> int | None:

        workspace = db.query(Workspace).filter(Workspace.owner_firebase_uid == firebase_uid).first()

        if not workspace:
            return None
        project = db.query(Project).filter(
            Project.workspace_id == workspace.id, Project.name == project_name
        ).first()
        if not project:
            return None
        model = db.query(MLModel).filter(
            MLModel.project_id == project.id, MLModel.name == model_name
        ).first()
        return model.id if model else None