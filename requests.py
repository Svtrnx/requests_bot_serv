from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import desc
from model import UserTable, TaskTable, ProxyTable, AccountTable
from connection import engine
import schema
from typing import List, Union
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError


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
            username            =  user_reg.username,
            key                 =  user_reg.key,
            hwid                =  user_reg.hwid,
            thread_count        =  user_reg.thread_count,
            application_count   =  user_reg.application_count,
            link_pinned         =  user_reg.link_pinned,
            sub_start           =  user_reg.sub_start,
            sub_end             =  user_reg.sub_end,
            role                =  user_reg.role,
            freezed             =  user_reg.freezed, 
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


def create_proxy_list(db: Session, proxy_media: List[schema.ProxySchema]):
	new_proxies = [
		ProxyTable(
			proxy_username=proxy.proxy_username,
			proxy_password=proxy.proxy_password,
			proxy_host=proxy.proxy_host,
			proxy_port=proxy.proxy_port,
			proxy_user_id=proxy.proxy_user_id,
            proxy_datetime=proxy.proxy_datetime,
		)
		for proxy in proxy_media
	]
	db.add_all(new_proxies)
	db.commit()
 
def get_proxy_list(db: Session, username: str):
    results = db.query(ProxyTable).filter(ProxyTable.proxy_user_id == username).all()

    db.close()

    return results

def delete_proxy(db: Session, proxy_list: List[str], user: str, delete_all_user_proxies: bool = False) -> Union[dict, None]:
    try:
        if delete_all_user_proxies:
            db.query(ProxyTable).filter(ProxyTable.proxy_user_id == user).delete(synchronize_session=False)
        else:
            proxy_ids = [int(proxy_id) for proxy_id in proxy_list]
            db.query(ProxyTable).filter(ProxyTable.id.in_(proxy_ids), ProxyTable.proxy_user_id == user).delete(synchronize_session=False)
        
        db.commit()
        
    except Exception as e:
        return {f"Error deleting proxies: {e}"}
    
    
def create_account_list(db: Session, user, account_media: List[schema.AccountSchema]):
    accounts = get_accounts_list(db, user)
    acc_logins = [account.acc_login for account in accounts]
    

    new_accounts = [
        AccountTable(
            acc_login=account.acc_login,
            acc_password=account.acc_password,
            acc_cookie=account.acc_cookie,
            acc_user_id=account.acc_user_id,
            acc_datetime=account.acc_datetime,
        )
        for account in account_media if account.acc_login not in acc_logins
    ]

    if new_accounts:
        db.add_all(new_accounts)
        db.commit()
 
 
def get_accounts_list(db: Session, username: str):
    results = db.query(AccountTable).filter(AccountTable.acc_user_id == username).all()

    db.close()

    return results

def delete_account(db: Session, account_list: List[str], user: str, delete_all_user_accounts: bool = False) -> Union[dict, None]:
    try:
        if delete_all_user_accounts:
            db.query(AccountTable).filter(AccountTable.acc_user_id == user).delete(synchronize_session=False)
        else:
            account_ids = [int(account_ids) for account_ids in account_list]
            db.query(AccountTable).filter(AccountTable.id.in_(account_ids), AccountTable.acc_user_id == user).delete(synchronize_session=False)
        
        db.commit()
        
    except Exception as e:
        return {f"Error deleting proxies: {e}"}
    
def delete_account_by_username(db: Session, account_list: List[str], user: str):
    try:
        db.query(AccountTable).filter(AccountTable.acc_login.in_(account_list), AccountTable.acc_user_id == user).delete(synchronize_session=False)
        
        db.commit()
        
    except Exception as e:
        return {f"Error deleting account by cookie: {e}"}
    
    
def take_users(db: Session, username: str):

    results = db.query(UserTable).filter(UserTable.username != username).all()
    return results

def delete_user(db: Session, user_id: str, user: str):
    try:
        user_to_delete = db.query(UserTable).filter(UserTable.id == user_id).first()

        if user_to_delete is None:
            return "User not found"

        if user_to_delete.role == "admin":
            raise HTTPException(status_code=400, detail="Access denied")

        db.query(UserTable).filter((UserTable.id == user_id) & (UserTable.username != user)).delete()

        db.commit()
        return "User deleted successfully"

    except SQLAlchemyError as e:
        db.rollback()
        return f"Error deleting user: {e}"
    
    
def get_tasks_list(db: Session, username: str):
    results = db.query(TaskTable).filter(TaskTable.task_user == username)\
                                 .order_by(desc(TaskTable.task_datetime))\
                                 .limit(80)\
                                 .all()

    db.close()

    return results