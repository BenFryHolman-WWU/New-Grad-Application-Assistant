import os, shutil, uuid
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel


DATABASE_URL = "sqlite:///./jobs.db"
engine       = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base         = declarative_base()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class Link(Base):
    __tablename__ = "links"
    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String,  nullable=False)
    url        = Column(String,  nullable=False)
    color      = Column(String,  default="#2563eb")
    created_at = Column(DateTime, default=datetime.utcnow)


class Contact(Base):
    __tablename__ = "contacts"
    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String,  nullable=False)
    title      = Column(String,  nullable=True)
    company    = Column(String,  nullable=True)
    email      = Column(String,  nullable=True)
    phone      = Column(String,  nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Application(Base):
    __tablename__ = "applications"
    id        = Column(Integer,  primary_key=True, index=True)
    company   = Column(String,   nullable=False)
    role      = Column(String,   nullable=False)
    type      = Column(String,   default="Full-time")
    status    = Column(String,   default="Applied")
    source    = Column(String,   nullable=True)
    location  = Column(String,   nullable=True)
    pay_range = Column(String,   nullable=True)
    job_url   = Column(String,   nullable=True)
    date      = Column(String,   nullable=False)
    app_notes = Column(Text,     nullable=True)


class ChecklistItem(Base):
    __tablename__ = "checklist"
    id   = Column(Integer, primary_key=True, index=True)
    text = Column(String,  nullable=False)
    done = Column(Boolean, default=False)


class Note(Base):
    __tablename__ = "notes"
    id    = Column(Integer, primary_key=True, index=True)
    key   = Column(String,  unique=True, nullable=False)
    value = Column(Text,    default="")


class Visit(Base):
    __tablename__ = "visits"
    id         = Column(Integer,  primary_key=True, index=True)
    board      = Column(String,   nullable=False)
    visited_at = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"
    id            = Column(Integer, primary_key=True, index=True)
    filename      = Column(String,  nullable=False)
    original_name = Column(String,  nullable=False)
    file_size     = Column(Integer, nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)

with SessionLocal() as _db:
    if _db.query(ChecklistItem).count() == 0:
        for text in [
            "Update resume for this specific role",
            "Tailor cover letter to job description",
            "Review job description for keywords",
            "Check company Glassdoor reviews",
            "Verify location / remote policy",
            "Set up job alerts on key boards",
            "Follow up after 1 week if no response",
        ]:
            _db.add(ChecklistItem(text=text))
    if _db.query(Note).count() == 0:
        for key in ["cover_letter", "job_search_notes"]:
            _db.add(Note(key=key, value=""))
    _db.commit()


class LinkCreate(BaseModel):
    name:  str
    url:   str
    color: str = "#2563eb"

class LinkOut(BaseModel):
    id: int; name: str; url: str; color: str; created_at: datetime
    model_config = {"from_attributes": True}


class ContactCreate(BaseModel):
    name:    str
    title:   Optional[str] = None
    company: Optional[str] = None
    email:   Optional[str] = None
    phone:   Optional[str] = None

class ContactOut(BaseModel):
    id: int; name: str
    title: Optional[str]; company: Optional[str]
    email: Optional[str]; phone:   Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}


class ApplicationCreate(BaseModel):
    company:   str
    role:      str
    type:      str           = "Full-time"
    status:    str           = "Applied"
    source:    Optional[str] = None
    location:  Optional[str] = None
    pay_range: Optional[str] = None
    job_url:   Optional[str] = None
    date:      str
    app_notes: Optional[str] = None

class ApplicationOut(BaseModel):
    id: int; company: str; role: str; type: str; status: str
    source: Optional[str]; location: Optional[str]; pay_range: Optional[str]
    job_url: Optional[str]; date: str; app_notes: Optional[str]
    model_config = {"from_attributes": True}


class ChecklistCreate(BaseModel):
    text: str

class ChecklistPatch(BaseModel):
    done: Optional[bool] = None
    text: Optional[str]  = None

class ChecklistOut(BaseModel):
    id: int; text: str; done: bool
    model_config = {"from_attributes": True}


class NoteUpsert(BaseModel):
    key: str; value: str

class NoteOut(BaseModel):
    id: int; key: str; value: str
    model_config = {"from_attributes": True}


class VisitCreate(BaseModel):
    board: str

class VisitOut(BaseModel):
    id: int; board: str; visited_at: datetime
    model_config = {"from_attributes": True}


class DocumentOut(BaseModel):
    id: int; original_name: str; file_size: Optional[int]; created_at: datetime
    model_config = {"from_attributes": True}


def get_db():
    """
    Yields a database session and closes it when the request finishes.
    Yields: Session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


links_router        = APIRouter(prefix="/links",        tags=["Links"])
contacts_router     = APIRouter(prefix="/contacts",     tags=["Contacts"])
applications_router = APIRouter(prefix="/applications", tags=["Applications"])
checklist_router    = APIRouter(prefix="/checklist",    tags=["Checklist"])
notes_router        = APIRouter(prefix="/notes",        tags=["Notes"])
visits_router       = APIRouter(prefix="/visits",       tags=["Visits"])
documents_router    = APIRouter(prefix="/documents",    tags=["Documents"])


@links_router.get("", response_model=List[LinkOut])
def get_links(db: Session = Depends(get_db)):
    """
    Returns all quick links ordered newest first.
    Returns: List[LinkOut]
    """
    return db.query(Link).order_by(Link.created_at.desc()).all()

@links_router.post("", response_model=LinkOut, status_code=201)
def create_link(link: LinkCreate, db: Session = Depends(get_db)):
    """
    Creates and persists a new quick link.
    Args: link (LinkCreate)
    Returns: LinkOut
    """
    obj = Link(**link.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@links_router.delete("/{link_id}")
def delete_link(link_id: int, db: Session = Depends(get_db)):
    """
    Deletes a quick link by ID.
    Args: link_id (int)
    Returns: dict {"ok": True}
    """
    obj = db.query(Link).filter(Link.id == link_id).first()
    if not obj: raise HTTPException(404, "Not found")
    db.delete(obj); db.commit()
    return {"ok": True}


@contacts_router.get("", response_model=List[ContactOut])
def get_contacts(db: Session = Depends(get_db)):
    """
    Returns all contacts ordered newest first.
    Returns: List[ContactOut]
    """
    return db.query(Contact).order_by(Contact.created_at.desc()).all()

@contacts_router.post("", response_model=ContactOut, status_code=201)
def create_contact(contact: ContactCreate, db: Session = Depends(get_db)):
    """
    Creates and persists a new contact.
    Args: contact (ContactCreate)
    Returns: ContactOut
    """
    obj = Contact(**contact.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@contacts_router.delete("/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    """
    Deletes a contact by ID.
    Args: contact_id (int)
    Returns: dict {"ok": True}
    """
    obj = db.query(Contact).filter(Contact.id == contact_id).first()
    if not obj: raise HTTPException(404, "Not found")
    db.delete(obj); db.commit()
    return {"ok": True}


@applications_router.get("", response_model=List[ApplicationOut])
def get_applications(db: Session = Depends(get_db)):
    """
    Returns all job applications ordered newest first.
    Returns: List[ApplicationOut]
    """
    return db.query(Application).order_by(Application.id.desc()).all()

@applications_router.post("", response_model=ApplicationOut, status_code=201)
def create_application(data: ApplicationCreate, db: Session = Depends(get_db)):
    """
    Creates and persists a new job application.
    Args: data (ApplicationCreate)
    Returns: ApplicationOut
    """
    obj = Application(**data.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@applications_router.patch("/{app_id}", response_model=ApplicationOut)
def update_application(app_id: int, data: ApplicationCreate, db: Session = Depends(get_db)):
    """
    Replaces all fields on an existing job application.
    Args: app_id (int), data (ApplicationCreate)
    Returns: ApplicationOut
    """
    obj = db.query(Application).filter(Application.id == app_id).first()
    if not obj: raise HTTPException(404, "Not found")
    for k, v in data.model_dump().items(): setattr(obj, k, v)
    db.commit(); db.refresh(obj)
    return obj

@applications_router.delete("/{app_id}")
def delete_application(app_id: int, db: Session = Depends(get_db)):
    """
    Deletes a job application by ID.
    Args: app_id (int)
    Returns: dict {"ok": True}
    """
    obj = db.query(Application).filter(Application.id == app_id).first()
    if not obj: raise HTTPException(404, "Not found")
    db.delete(obj); db.commit()
    return {"ok": True}


@checklist_router.post("/reset")
def reset_checklist(db: Session = Depends(get_db)):
    """
    Marks every checklist item as incomplete.
    Returns: dict {"ok": True}
    """
    db.query(ChecklistItem).update({"done": False}); db.commit()
    return {"ok": True}

@checklist_router.get("", response_model=List[ChecklistOut])
def get_checklist(db: Session = Depends(get_db)):
    """
    Returns all checklist items.
    Returns: List[ChecklistOut]
    """
    return db.query(ChecklistItem).all()

@checklist_router.post("", response_model=ChecklistOut, status_code=201)
def create_checklist_item(item: ChecklistCreate, db: Session = Depends(get_db)):
    """
    Creates a new checklist item.
    Args: item (ChecklistCreate)
    Returns: ChecklistOut
    """
    obj = ChecklistItem(text=item.text)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@checklist_router.patch("/{item_id}", response_model=ChecklistOut)
def patch_checklist_item(item_id: int, patch: ChecklistPatch, db: Session = Depends(get_db)):
    """
    Updates the text or completion state of a checklist item.
    Args: item_id (int), patch (ChecklistPatch)
    Returns: ChecklistOut
    """
    obj = db.query(ChecklistItem).filter(ChecklistItem.id == item_id).first()
    if not obj: raise HTTPException(404, "Not found")
    if patch.done is not None: obj.done = patch.done
    if patch.text is not None: obj.text = patch.text
    db.commit(); db.refresh(obj)
    return obj

@checklist_router.delete("/{item_id}")
def delete_checklist_item(item_id: int, db: Session = Depends(get_db)):
    """
    Deletes a checklist item by ID.
    Args: item_id (int)
    Returns: dict {"ok": True}
    """
    obj = db.query(ChecklistItem).filter(ChecklistItem.id == item_id).first()
    if not obj: raise HTTPException(404, "Not found")
    db.delete(obj); db.commit()
    return {"ok": True}


@notes_router.get("", response_model=List[NoteOut])
def get_notes(db: Session = Depends(get_db)):
    """
    Returns all notes.
    Returns: List[NoteOut]
    """
    return db.query(Note).all()

@notes_router.post("", response_model=NoteOut)
def upsert_note(note: NoteUpsert, db: Session = Depends(get_db)):
    """
    Creates a note or updates its value if the key already exists.
    Args: note (NoteUpsert)
    Returns: NoteOut
    """
    obj = db.query(Note).filter(Note.key == note.key).first()
    if obj:
        obj.value = note.value
    else:
        obj = Note(key=note.key, value=note.value); db.add(obj)
    db.commit(); db.refresh(obj)
    return obj


@visits_router.get("", response_model=List[VisitOut])
def get_visits(db: Session = Depends(get_db)):
    """
    Returns all board visits ordered most recent first.
    Returns: List[VisitOut]
    """
    return db.query(Visit).order_by(Visit.visited_at.desc()).all()

@visits_router.post("", response_model=VisitOut, status_code=201)
def create_visit(visit: VisitCreate, db: Session = Depends(get_db)):
    """
    Records a new visit to a job board.
    Args: visit (VisitCreate)
    Returns: VisitOut
    """
    obj = Visit(board=visit.board)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@documents_router.get("", response_model=List[DocumentOut])
def get_documents(db: Session = Depends(get_db)):
    """
    Returns all uploaded documents ordered newest first.
    Returns: List[DocumentOut]
    """
    return db.query(Document).order_by(Document.created_at.desc()).all()

@documents_router.post("", response_model=DocumentOut, status_code=201)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Saves an uploaded file to disk and records its metadata.
    Args: file (UploadFile)
    Returns: DocumentOut
    """
    ext    = os.path.splitext(file.filename or "")[1]
    stored = f"{uuid.uuid4().hex}{ext}"
    path   = os.path.join(UPLOAD_DIR, stored)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    size = os.path.getsize(path)
    obj  = Document(filename=stored, original_name=file.filename or stored, file_size=size)
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

@documents_router.get("/{doc_id}/download")
def download_document(doc_id: int, db: Session = Depends(get_db)):
    """
    Streams a document file as a download attachment.
    Args: doc_id (int)
    Returns: FileResponse
    """
    obj = db.query(Document).filter(Document.id == doc_id).first()
    if not obj: raise HTTPException(404, "Not found")
    path = os.path.join(UPLOAD_DIR, obj.filename)
    if not os.path.exists(path): raise HTTPException(404, "File missing on disk")
    return FileResponse(path, filename=obj.original_name, media_type="application/octet-stream")

@documents_router.delete("/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    """
    Deletes a document record and removes its file from disk.
    Args: doc_id (int)
    Returns: dict {"ok": True}
    """
    obj = db.query(Document).filter(Document.id == doc_id).first()
    if not obj: raise HTTPException(404, "Not found")
    path = os.path.join(UPLOAD_DIR, obj.filename)
    if os.path.exists(path): os.remove(path)
    db.delete(obj); db.commit()
    return {"ok": True}


app = FastAPI(title="Job Application Assistant")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

for router in (links_router, contacts_router, applications_router,
               checklist_router, notes_router, visits_router, documents_router):
    app.include_router(router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_index():
    """
    Serves the main frontend HTML page.
    Returns: FileResponse
    """
    return FileResponse("static/index.html")
