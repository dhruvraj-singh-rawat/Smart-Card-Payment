from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
 
Base = declarative_base()

class UserTable(Base):
    __tablename__ = 'user_table'
   
    pin = Column(String(10))    
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    typeCard = Column(String(5))
    rfidno  = Column(String(50))
    picture = Column(String(250))
    userLevel = Column(String(250))
    id = Column(Integer, primary_key = True)

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'email'           : self.email,
           'rfidno'          : self.rfidno,
           'pin'              : self.pin,
           'userLevel'        : self.userLevel,
       
       }

class StatementHistory(Base):
    __tablename__ = 'statement_history'
   
    
    
    id = Column(Integer, primary_key = True)
    email = Column(String(250))
    time_stamp = Column(String(250))
    amount_deposit = Column(String(250))
    amount_withdraw = Column(String(250))

    statement_history_id = Column(Integer,ForeignKey('user_table.id'))
    user_table = relationship(UserTable)
    
    

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'time_stamp'         : self.time_stamp,
           'email'           : self.email,
           'amount_deposit'         : self.amount_deposit,
           'amount_withdraw'              : self.amount_withdraw,
       }

class StatementTable(Base):
    __tablename__ = 'statement_table'


    
    id = Column(Integer, primary_key = True)    
    balance = Column(String(8))    
    email = Column(String(250))

    statement_id = Column(Integer,ForeignKey('user_table.id'))
    user_table = relationship(UserTable)


    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {          
           
           'balance'         : self.balance,
           'email'         : self.email,

       }



engine = create_engine('sqlite:///digitalpayment.db')
 

Base.metadata.create_all(engine)
