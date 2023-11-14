from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from project.models.role import Role  

# Tạo engine và session
engine = create_engine('mysql+mysqlconnector://root:001122@localhost/booking_v3')
Session = sessionmaker(bind=engine)
session = Session()

# Tạo và thêm dữ liệu
role_manager = Role(name='manager')

session.add(role_manager)


# Commit các thay đổi vào cơ sở dữ liệu
session.commit()

# Đóng session
session.close()