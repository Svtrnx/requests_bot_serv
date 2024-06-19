from sqlalchemy.orm import sessionmaker, Session
from model import UserTable, TaskTable
from connection import engine
import schema


def get_user_only_by_username(db: Session, username: str):
    try:
        record = db.query(UserTable).filter((UserTable.username == username)).first()
        return record

    except Exception as e:
        db.rollback()
        return f"Error getting user by username: {e}"

def get_user_by_username(db: Session, username: str, user_key: str, hwid: str):
    try:
        record = db.query(UserTable).filter(
            (UserTable.username == username) & (UserTable.key == user_key) & (UserTable.hwid == hwid)
        ).first()
        
        print(record)

        return record

    except Exception as e:
        db.rollback()
        return f"Error getting user by params: {e}"

def create_user(db: Session, user_reg: schema.UserSchema):
    try:
        new_user_reg = UserTable(
            username        =  user_reg.username,
            key             =  user_reg.key,
            hwid            =  user_reg.hwid,
            sub_start       =  user_reg.sub_start,
            sub_end         =  user_reg.sub_end,
            role            =  user_reg.role,
            freezed         =  user_reg.freezed, 
        )
        db.add(new_user_reg)
        db.commit()
        db.refresh(new_user_reg)
        return new_user_reg

    except Exception as e:
        db.rollback()
        return f"Error to create user: {e}"
    
def create_task_func(db: Session, task_reg: schema.TaskSchema):
    try:
        new_task_reg = TaskTable(
            task_status         =  task_reg.task_status,
            task_id             =  task_reg.task_id,
            task_delay          =  task_reg.task_delay,
            task_user           =  task_reg.task_user,
            task_datetime       =  task_reg.task_datetime,
            threads_count       =  task_reg.threads_count,
            task_work           =  task_reg.task_work,
        )
        db.add(new_task_reg)
        db.commit()
        db.refresh(new_task_reg)
        return new_task_reg

    except Exception as e:
        db.rollback()
        return f"Error to create task: {e}"
