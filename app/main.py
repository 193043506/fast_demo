from fastapi import FastAPI, Path, Query
from decimal import Decimal

from pydantic import BaseModel
# 创建应用对象，后续通过 app 注册接口。
app = FastAPI()
categories = [
    {"id": 1, "name": "饮料", "create_time": "2026-10-13 08:00:00"},
    {"id": 2, "name": "数码配件", "create_time": "2026-10-13 08:00:00"},
    {"id": 3, "name": "零食", "create_time": "2026-10-13 08:00:00"},
]

products = [
    {
        "id": 1,
        "category_id": 1,
        "name": "矿泉水",
        "price": "3.50",
        "stock": 100,
        "shelf_status": True,
        "create_time": "2026-10-13 09:00:00",
    },
    {
        "id": 2,
        "category_id": 1,
        "name": "可乐",
        "price": "5.00",
        "stock": 80,
        "shelf_status": True,
        "create_time": "2026-10-13 10:00:00",
    },
    {
        "id": 3,
        "category_id": 2,
        "name": "USB 数据线",
        "price": "19.90",
        "stock": 0,
        "shelf_status": False,
        "create_time": "2026-10-13 11:00:00",
    },
]



class ProductCreate(BaseModel):
    """描述新增商品时客户端可以提交的字段。"""
    category_id: int
    name: str
    price: Decimal
    stock: int = 0
    shelf_status: bool = True


# 将 GET 方法和根路径 / 关联到下面的函数。
@app.get("/")
def root():
    """不接收参数，返回服务运行中的字典数据"""
    return {"message": "FastAPI Service is Running"}
@app.get("/hello")
def hello():
    """不接收参数，返回包含中文问候的字典。"""
    return {"message": "你好，FastAPI"}



@app.get("/products/count")
def count_products():
    """不接收参数，返回全部内存商品的数量。"""
    return {"total": len(products)}


@app.get("/products/{product_id}")
def read_product(product_id: int = Path(gt = 0)):
    for product in products:
        if product["id"] == product_id:
            return product
    return None



@app.get("/products")
def list_products(
    category_id: int | None = Query(
        default=None,gt = 0),
        keyword: str | None = Query(
        default=None, max_length=50, description="查询关键字，根据商品名称筛选"
    ),
    page: int = Query(default=1, ge=1, description="页码，从 1 开始"),
    page_size: int = Query(default=2, ge=1, le=100),
):
    
    filter_products = products

    if category_id is not None:
        temp = []
        for product in filter_products:
            if product["category_id"] == category_id:
                temp.append(product)

        filter_products = temp

    #and采用短路求值：前一项不成立时，不执行后一项，所以 keyword 为 None 时不会调用 .strip()。
    if keyword and keyword.strip():
        search_text = keyword.strip().lower()
        temp = []
        for product in filter_products:
            if(search_text in product["name"].lower()
               ):
                temp.append(product)
        filter_products = temp
                
    start = (page - 1) *page_size
    end = start + page_size
    return{
        "items":filter_products[start:end],
        "total":len(filter_products),
        "page":page,
        "page_size":page_size,
    }



@app.post("/peoducts")
def create_product(payload:ProductCreate):
    return payload.model_dump()