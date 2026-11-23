from datetime import datetime, timezone, timedelta

from fastapi import FastAPI, HTTPException, Path, Query
from decimal import Decimal

from pydantic import BaseModel, Field
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
    #有 default = 可选字段；没写 default 的必填  
    category_id: int = Field(
        gt = 0, description="商品分类的ID，必须是正整数")
    name: str = Field(min_length=1,max_length=50,description="商品名称，必填，不超过50个字符")
    price: Decimal = Field(ge = 0,decimal_places=2,max_digits=8,description="商品价格，最大保留两位小数")
    stock: int = Field(ge=0,description="库存，不小于0")
    shelf_status: bool = Field(default=False,description="上架状态")


class ProductUpdate(BaseModel):
    #修改商品的字段
    """ProductUpdate 是修改用的——PATCH 的语义是"只改我提交的字段"。
    所以每个字段都必须允许不传，于是全部写成 类型 | None，
    default None。这里的 None 不代表"把字段改成空"，而是"不要动这个字段的值"。
    """
    category_id:int | None = Field(default=None,gt = 0,description = "商品分类的ID，必须是正整数")
    name: str | None = Field(default=None,min_length=1,max_length=50,description="商品名称，必填，不超过50个字符")
    price: Decimal | None = Field(default=None,ge = 0,decimal_places=2,max_digits=8,description="商品价格，最大保留两位小数")
    stock: int | None= Field(default=None,ge=0,description="库存，不小于0")
    shelf_status: bool | None= Field(default=None,description="上架状态")

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
    
    return get_product_or_404(product_id)

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

@app.post("/products")
def create_product(payload:ProductCreate):
    """先检查商品名称是否为空，然后在检查分类id有没有"""
    if payload:
        name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400,detail="商品名称不能为空")
    id_exists = False
    for category in categories:
        if payload.category_id == category["id"]:
            id_exists = True
    if not id_exists:
        raise HTTPException(status_code=400,detail="分类ID不存在")
    payload.name = name
    next_id = max((product["id"] for product in products),default=0)+1
    product = {
        "id":next_id,
        **payload.model_dump(),
        "create_time":datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    }
    products.append(product)
    return product

#对于增删改查没有这个商品id的,抛出异常,有的话即返回那个item
def get_product_or_404(product_id: int)->dict:
    for item in products:
        if item["id"] == product_id:
            return item
    raise HTTPException(status_code=404,detail="商品不存在")

# PATCH：只修改提交的字段
@app.patch("/products/{product_id}")
def update_product(payload: ProductUpdate,
                   product_id:int = Path(gt=0)):
    product = get_product_or_404(product_id)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400,detail="至少提交一个修改字段")
    """
changes.keys()    # 只要键：'name', 'stock', ...
changes.values()  # 只要值：'巧克力', 50, ...
changes.items()   # 键和值都要：('name', '巧克力'), ('stock', 50),
"""
    for field, value in changes.items():
        if value is None:
            raise HTTPException(status_code=400,detail=f"字段{field}的值不允许为null")
    if "name" in changes:
        changes["name"] = changes["name"].strip()
        if not changes["name"]:
            raise HTTPException(status_code=400,detail="商品名称不能为空")
       #原始写法
        # if "categoriy_id" in changes:
        #     category_id = changes["category_id"]
        #     found = False
        #     for category in categories:
        #         if category["id"] == category_id:
        #             found = True
        #             break
        #     if not False:
        #         raise HTTPException(status_code=400,detail="商品分类不存在")
            
            
                #通俗写法
    if "category_id" in changes:
        if not any( category["id"] == changes["category_id"] for category in categories):
            raise HTTPException(status_code=400,detail="商品分类不存在")
    product.update(changes)
    return product

@app.delete("/products/{product_id}")
def delete_product(product_id: int = Path(gt=0)):
    product = get_product_or_404(product_id)
    products.remove(product)
    return {"message":"商品删除成功"}
