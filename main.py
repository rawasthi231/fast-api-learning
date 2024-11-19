import uvicorn
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import (
    FastAPI,
    Path,
    Query,
    Request,
    Form,
    File,
    UploadFile,
    Cookie,
    Depends,
    WebSocket,
)
from typing import List, Tuple
from pydantic import BaseModel, Field
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session

from models.Book import Book, Books, session


origins = [
    "http://127.0.0.1:8000",
    "http://localhost",
    "http://localhost:8080",
]

import shutil

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Student(BaseModel):
    id: int
    name: str = Field(None, title="name of student", max_length=10)
    subjects: List[str] = []


@app.middleware("http")
async def addmiddleware(request: Request, call_next):
    print("Middleware works!")
    response = await call_next(request)
    return response


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/socket", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("socket.html", {"request": request})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")


@app.get("/hello/{name}", response_class=HTMLResponse)
async def hello(request: Request, name: str):
    return templates.TemplateResponse(
        "hello.html", {"request": request, "name": name.capitalize()}
    )


@app.get("/message")
async def send_message():
    ret = """
    <html>
    <body>
    <h2>Hello World!</h2>
    </body>
    </html>
    """
    return HTMLResponse(content=ret)


@app.get("/hello")  # /hello?name=John&age=25
async def hello(name: str, age: int):
    return {"name": name.capitalize(), "age": age}


# @app.get("/hello/{name}/{age}") # /hello/John/25?percent=50
# async def hello(*, name: str=Path(...,min_length=3 , max_length=10), age: int = Path(..., ge=1, le=100),
#       percent:float=Query(..., ge=0, le=100)):
#    return {"name": name, "age":age, "percent":percent}


@app.get("/hello/{name}/{age}")  # /hello/John/25
async def hello(
    *,
    name: str = Path(..., min_length=3, max_length=10),
    age: int = Path(..., ge=1, le=100),
):
    return {"name": name, "age": age}


data = {
    "id": 1,
    "name": "Ravikumar",
    "subjects": ["Eng", "Maths", "Sci"],
}


@app.get("/student")
async def get_student():
    s1 = Student(**data)
    return s1.model_dump()


@app.post("/student")
async def create_student(student: Student):
    return student


@app.post("/student/{college}")
async def create_student_2(college: str, age: int, student: Student):
    retval = {"college": college, "age": age, **student.model_dump()}
    return retval


@app.get("/login/", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


class User(BaseModel):
    username: str
    password: str


@app.post("/login", response_model=User)
async def login(nm: str = Form(...), pwd: str = Form(...)):
    return User(username=nm, password=pwd)


@app.get("/upload/", response_class=HTMLResponse)
async def upload(request: Request):
    return templates.TemplateResponse("file-upload.html", {"request": request})


@app.post("/upload-file/")
async def create_upload_file(file: UploadFile = File(...)):
    with open("destination.png", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename}


@app.post("/cookie/")
def create_cookie():
    content = {"message": "cookie set"}
    response = JSONResponse(content=content)
    response.set_cookie(key="username", value="admin")
    return response


@app.get("/readcookie/")
async def read_cookie(username: str = Cookie(None)):
    return {"username": username}


class students(BaseModel):
    id: int
    name: str = Field(None, title="name of student", max_length=10)
    marks: List[int] = []
    percent_marks: float


class percent(BaseModel):
    id: int
    name: str = Field(None, title="name of student", max_length=10)
    percent_marks: float


@app.post("/marks", response_model=percent)
async def get_percent(s1: students):
    s1.percent_marks = sum(s1.marks) / 2
    return s1


class supplier(BaseModel):
    supplierID: int
    supplierName: str


class product(BaseModel):
    productID: int
    prodname: str
    price: int
    supp: supplier


class customer(BaseModel):
    custID: int
    custname: str
    prod: Tuple[product]


@app.post("/invoice")
async def getInvoice(c1: customer):
    return c1


# data = []


# @app.post("/book")
# def add_book(book: Book):
#     data.append(book.model_dump())
#     return data


# @app.get("/books")
# def get_books():
#     return data


# @app.get("/book/{id}")
# def get_book(id: int):
#     id = id - 1
#     return data[id]


# @app.put("/book/{id}")
# def add_book(id: int, book: Book):
#     data[id - 1] = book
#     return data


# @app.delete("/book/{id}")
# def delete_book(id: int):
#     data.pop(id - 1)
#     return data


def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()


@app.post("/add_new", response_model=Book)
def add_book(b1: Book, db: Session = Depends(get_db)):
    try:
        print(b1)
        bk = Books(id=b1.id, title=b1.title, author=b1.author, publisher=b1.publisher)

        db.add(bk)
        db.commit()
        db.refresh(bk)
        return Books(**b1.model_dump())
    except Exception as e:
        print(e)
        return {"message": str(e)}


@app.get("/books", response_model=List[Book])
def get_books(db: Session = Depends(get_db)):
    recs = db.query(Books).all()
    return recs


@app.get("/book/{id}", response_model=Book)
def get_book(id: int, db: Session = Depends(get_db)):
    return db.query(Books).filter(Books.id == id).first()


@app.put("/update-book/{id}", response_model=Book)
def update_book(id: int, book: Book, db: Session = Depends(get_db)):
    print(book)
    b1 = db.query(Books).filter(Books.id == id).first()
    b1.id = book.id
    b1.title = book.title
    b1.author = book.author
    b1.publisher = book.publisher
    db.commit()
    return db.query(Books).filter(Books.id == id).first()


@app.delete("/delete-book/{id}")
def del_book(id: int, db: Session = Depends(get_db)):
    try:
        db.query(Books).filter(Books.id == id).delete()
        db.commit()
    except Exception as e:
        raise Exception(e)
    return {"delete status": "success"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
