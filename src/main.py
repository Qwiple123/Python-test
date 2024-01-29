import datetime as dt
from fastapi import FastAPI, HTTPException, Query
from database import engine, Session, Base, City, User, Picnic, PicnicRegistration
from external_requests import CheckCityExisting, GetWeatherRequest
from models import RegisterUserRequest, UserModel
from sqlalchemy import desc

app = FastAPI()


@app.get('/create-city/', summary='Create City', description='Создание города по его названию')
def create_city(city: str = Query(description="Название города", default=None)):
    if city is None:
        raise HTTPException(status_code=400, detail='Параметр city должен быть указанd')
    check = CheckCityExisting()
    if not check.check_existing(city):
        raise HTTPException(status_code=400, detail='Параметр city должен быть существующим городомd')

    city_object = Session().query(City).filter(City.name == city.capitalize()).first()
    if city_object is None:
        city_object = City(name=city.capitalize())
        s = Session()
        s.add(city_object)
        s.commit()

    return {'id': city_object.id, 'name': city_object.name, 'weather': city_object.weather}


@app.get('/get-cities/', summary='Get Cities')
def cities_list(q: str = Query(description="Название города", default=None)):
    """
    Получение списка городов
    """
    
    cities = Session().query(City).all()

    if q is not None:
        #Проверка является ли q подстрокой названия города, если до то возвращает этот город
        return [{'id': city.id, 'name': city.name, 'weather': city.weather} for city in cities if q in city.name]
    
    if q is None:
        return [{'id': city.id, 'name': city.name, 'weather': city.weather} for city in cities]

@app.post('/users-list/', summary='')
def users_list(sort: str = Query(description="Сортировка (Поубыванию - asc, По возрастанию - desc)", default=None)):
    """
    Список пользователей
    """
    
    if sort == 'asc':
        users = Session().query(User).order_by(User.age)
    elif sort == 'desc':
        users = Session().query(User).order_by(desc(User.age))
    elif sort == None:
        users = Session().query(User).all()

    return [{
        'id': user.id,
        'name': user.name,
        'surname': user.surname,
        'age': user.age,
    } for user in users]


@app.post('/register-user/', summary='CreateUser', response_model=UserModel)
def register_user(user: RegisterUserRequest):
    """
    Регистрация пользователя
    """
    user_object = User(**user.dict())
    s = Session()
    s.add(user_object)
    s.commit()

    return UserModel.from_orm(user_object)


@app.get('/all-picnics/', summary='All Picnics', tags=['picnic'])
def all_picnics(datetime: dt.datetime = Query(default=None, description='Время пикника (по умолчанию не задано)'),
                past: bool = Query(default=True, description='Включая уже прошедшие пикники')):
    """
    Список всех пикников
    """
    picnics = Session().query(Picnic)
    if datetime is not None:
        picnics = picnics.filter(Picnic.time == datetime)
    if not past:
        picnics = picnics.filter(Picnic.time >= dt.datetime.now())

    return [{
        'id': pic.id,
        'city': Session().query(City).filter(City.id == pic.city_id).first().name,
        'time': pic.time,
        'users': [
            {
                'id': pr.user.id,
                'name': pr.user.name,
                'surname': pr.user.surname,
                'age': pr.user.age,
            }
            for pr in Session().query(PicnicRegistration).filter(PicnicRegistration.picnic_id == pic.id)],
    } for pic in picnics]


@app.get('/picnic-add/', summary='Picnic Add', tags=['picnic'])
def picnic_add(city_id: int = None, datetime: dt.datetime = None):
    p = Picnic(city_id=city_id, time=datetime)
    s = Session()
    s.add(p)
    s.commit()
    #Ошибка была в указании id города для city(указывался id обьекта пикника а не id города в котором будет пикник)
    #Такая же ошибка была в all_picnics
    return {
        'id': p.id,
        'city': Session().query(City).filter(City.id == p.city_id).first().name,
        'time': p.time,
    }


@app.get('/picnic-register/', summary='Picnic Registration', tags=['picnic'])
def register_to_picnic(picnic_id: int = None, user_id: int = None):
    """
    Регистрация пользователя на пикник
    """
    
    picnic_object = PicnicRegistration(user_id = user_id, picnic_id = picnic_id)
    s = Session()
    s.add(picnic_object)
    s.commit()
    return {'id': picnic_object.id, 'city': Session().query(City).filter(City.id == picnic_object.picnic.city_id).first().name, 'time': picnic_object.picnic.time, 'user_id': picnic_object.user_id, 'name': picnic_object.user.name} 

