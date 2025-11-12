"""Models for old database tables with 'old_' prefix - Read-only access."""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from app.database import Base


class OldAccMaster(Base):
    """Old Account Master table - Read only."""
    __tablename__ = "old_accmaster"
    
    slno = Column(Integer, primary_key=True)
    accode = Column(String(6))
    accname = Column(String(50))
    opbaldeb = Column(Float)
    opbalcre = Column(Float)
    curbaldeb = Column(Float)
    curbalcre = Column(Float)
    accttype = Column(String(5))
    schedno = Column(Integer)
    opbaldate = Column(DateTime)
    conscno = Column(Integer)
    
    __table_args__ = {'extend_existing': True}


class OldAccountLedger(Base):
    """Old Account Ledger table - Read only."""
    __tablename__ = "old_account_ledger"
    
    ID = Column(Integer, primary_key=True)
    date = Column(DateTime)
    jlno = Column(String(50))
    description = Column(String(50))
    debit = Column(Float)
    credit = Column(Float)
    register = Column(String(255))
    
    __table_args__ = {'extend_existing': True}


class OldCustomer(Base):
    """Old Customer table - Read only."""
    __tablename__ = "old_customer"
    
    pno = Column(String(50), primary_key=True)
    name = Column(String(50))
    address = Column(String(250))
    phoneno = Column(String(50))
    mobile = Column(String(50))
    int_date = Column(String(50))
    cust_refno = Column(String(50))
    pictures = Column(Text)
    entrydate = Column(DateTime)
    
    __table_args__ = {'extend_existing': True}


class OldJewelDesc(Base):
    """Old Jewel Description (Pledge) table - Read only."""
    __tablename__ = "old_jewel_desc"
    
    jlno = Column(String(50), primary_key=True)
    laon_date = Column(DateTime)
    party_details = Column(String(250))
    jewel_weight = Column(String(50))
    jewel_description = Column(Text)
    loan_amount = Column(Float)
    loan_ret_amount = Column(Float)
    loan_interest = Column(Float)
    loan_ret_date = Column(DateTime)
    actual_maturity = Column(DateTime)
    maturity_date = Column(DateTime)
    pcode = Column(String(10))
    vno = Column(Integer)
    intper = Column(Float)
    rvno = Column(Integer)
    splace = Column(String(50))
    sdetails = Column(String(50))
    currate = Column(Float)
    curamount = Column(Float)
    bvno = Column(Integer)
    brvno = Column(Integer)
    orgweight = Column(Float)
    jeweltype = Column(String(50))
    register = Column(String(50))
    notes = Column(String(50))
    tagcode = Column(String(255))
    notice1date = Column(DateTime)
    notice2date = Column(DateTime)
    notice3date = Column(DateTime)
    days = Column(Integer)
    auts = Column(Integer)
    pictures = Column(String(255))
    
    __table_args__ = {'extend_existing': True}


class OldJewelDetails(Base):
    """Old Jewel Details (Pledge Items) table - Read only."""
    __tablename__ = "old_jewel_details"
    
    sno = Column(Integer, primary_key=True)
    laon_date = Column(DateTime)
    jlno = Column(String(50))
    register = Column(String(50))
    itemdet = Column(String(255))
    qty = Column(Float)
    grosswt = Column(Float)
    netweight = Column(Float)
    notes = Column(String(50))
    
    __table_args__ = {'extend_existing': True}
