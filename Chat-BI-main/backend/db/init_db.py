import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import inspect
from models.base import Base
from models import SysUser, SysAiModelConfig, SysConversation, SysConversationMessage
from db.session import engine, async_session


async def init_db():
    """初始化数据库，创建所有表（如果不存在）"""
    async with engine.begin() as conn:
        try:
            # 检查是否已有表存在
            def check_tables(connection):
                inspector = inspect(connection)
                existing_tables = inspector.get_table_names()
                return existing_tables

            existing_tables = await conn.run_sync(check_tables)

            if existing_tables:
                logging.info(f"数据库已初始化，现有 {len(existing_tables)} 个表")
            else:
                logging.info("首次初始化数据库，正在创建表...")

            # create_all 会自动检查表是否存在（checkfirst=True 是默认值）
            # 只创建不存在的表，不会重复创建
            await conn.run_sync(Base.metadata.create_all)

            if not existing_tables:
                logging.info("数据库表创建完成")

        except SQLAlchemyError as e:
            logging.error(f"数据库操作错误: {e}")
            raise


async def insert_default_data():
    """插入默认数据（如默认管理员账户）"""
    try:
        async with async_session() as session:
            try:
                # 检查是否已存在管理员账户
                from sqlalchemy import select
                result = await session.execute(
                    select(SysUser).where(SysUser.username == 'admin')
                )
                existing_admin = result.scalar_one_or_none()

                if not existing_admin:
                    # 创建默认管理员账户
                    from passlib.context import CryptContext
                    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

                    admin_user = SysUser(
                        username='admin',
                        email='admin@chatbi.com',
                        password_hash=pwd_context.hash('admin123'),
                        full_name='系统管理员',
                        is_active=True,
                        is_superuser=True
                    )
                    session.add(admin_user)
                    await session.commit()
                    logging.info("默认管理员账户创建成功: username=admin, password=admin123")
                else:
                    logging.info("管理员账户已存在，跳过创建")

            except SQLAlchemyError as e:
                logging.error(f"插入默认数据错误: {e}")
                await session.rollback()
                raise
            except Exception as e:
                logging.error(f"处理默认数据时发生错误: {e}")
                await session.rollback()
                # 如果是密码加密库不存在的错误，提供友好提示
                if "passlib" in str(e):
                    logging.warning("passlib库未安装，跳过创建默认管理员账户")
                else:
                    raise

    except Exception as e:
        logging.error(f"插入默认数据过程中发生错误: {e}")
