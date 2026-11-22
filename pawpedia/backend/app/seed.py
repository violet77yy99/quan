"""初始化数据：默认账号 + 8 个犬种科普卡片。"""

from sqlalchemy.orm import Session

from .models import Breed, User
from .security import hash_password

BREEDS = [
    {
        "slug": "beagle",
        "name_cn": "比格",
        "name_en": "Beagle",
        "intro": "比格犬是来自英国的中型猎犬，长着一对大耳朵和永远在线的好奇心。嗅觉非常灵敏，性格活泼亲人，是很多家庭的开心果。",
        "personality": "活泼,好奇,贪吃,友善",
        "size_category": "中型犬",
        "difficulty": "中等",
        "origin": "英国",
        "market_price": "800 - 2500 元",
        "image_url": "/static/breeds/beagle.jpg",
        "is_dog": True,
    },
    {
        "slug": "chinese-rural-dog",
        "name_cn": "中华田园犬",
        "name_en": "Chinese Rural Dog",
        "intro": "中华田园犬是中国本土犬的统称，俗称“土狗”。它们适应力强、忠诚护家，外貌差异很大，是陪伴了很多人的童年伙伴。",
        "personality": "忠诚,警觉,聪明,适应力强",
        "size_category": "中型犬",
        "difficulty": "容易",
        "origin": "中国",
        "market_price": "领养为主，0 - 500 元",
        "image_url": "/static/breeds/chinese-rural-dog.jpg",
        "is_dog": True,
    },
    {
        "slug": "poodle",
        "name_cn": "泰迪",
        "name_en": "Poodle (Teddy)",
        "intro": "泰迪通常指修剪成泰迪造型的贵宾犬，聪明、黏人、掉毛少。体型小巧，适合公寓家庭，但需要定期美容和陪伴。",
        "personality": "聪明,黏人,活泼,掉毛少",
        "size_category": "小型犬",
        "difficulty": "中等",
        "origin": "法国 / 德国",
        "market_price": "1000 - 5000 元",
        "image_url": "/static/breeds/poodle.jpg",
        "is_dog": True,
    },
    {
        "slug": "samoyed",
        "name_cn": "萨摩耶",
        "name_en": "Samoyed",
        "intro": "萨摩耶来自西伯利亚，一身雪白长毛和“微笑脸”非常有辨识度。性格温顺友好，但运动量和梳毛工作量都不小。",
        "personality": "温顺,友好,爱笑,精力旺盛",
        "size_category": "大型犬",
        "difficulty": "中等",
        "origin": "西伯利亚",
        "market_price": "1500 - 6000 元",
        "image_url": "/static/breeds/samoyed.jpg",
        "is_dog": True,
    },
    {
        "slug": "border-collie",
        "name_cn": "边牧",
        "name_en": "Border Collie",
        "intro": "边境牧羊犬是公认的高智商犬种，学习能力强、精力充沛。它们需要大量运动和脑力游戏，不适合长期关在家里。",
        "personality": "聪明,精力充沛,学习能力强,需要陪伴",
        "size_category": "中型犬",
        "difficulty": "较难",
        "origin": "英国",
        "market_price": "1500 - 5000 元",
        "image_url": "/static/breeds/border-collie.jpg",
        "is_dog": True,
    },
    {
        "slug": "golden-retriever",
        "name_cn": "金毛",
        "name_en": "Golden Retriever",
        "intro": "金毛寻回犬性格温顺、耐心、对人友好，是典型的家庭伴侣犬。喜欢游泳和衔取，掉毛量较大，需要定期梳理。",
        "personality": "温顺,友善,耐心,适合家庭",
        "size_category": "大型犬",
        "difficulty": "中等",
        "origin": "英国",
        "market_price": "1200 - 5000 元",
        "image_url": "/static/breeds/golden-retriever.jpg",
        "is_dog": True,
    },
    {
        "slug": "corgi",
        "name_cn": "柯基",
        "name_en": "Welsh Corgi",
        "intro": "柯基是来自威尔士的小型牧牛犬，短腿大屁股非常可爱。性格活泼勇敢、聪明爱叫，需要控制体重和保护腰椎。",
        "personality": "活泼,勇敢,聪明,爱叫",
        "size_category": "小型犬",
        "difficulty": "中等",
        "origin": "英国威尔士",
        "market_price": "1500 - 6000 元",
        "image_url": "/static/breeds/corgi.jpg",
        "is_dog": True,
    },
    {
        "slug": "orange-cat",
        "name_cn": "橘猫",
        "name_en": "Orange Tabby",
        "intro": "橘猫不是独立品种，而是橙色虎斑猫的统称。它们通常亲人、贪吃、性格慵懒，是本项目特意加入的“非犬类”干扰项。",
        "personality": "亲人,贪吃,慵懒,独立",
        "size_category": "其他",
        "difficulty": "容易",
        "origin": "世界各地",
        "market_price": "领养为主，0 - 800 元",
        "image_url": "/static/breeds/orange-cat.jpg",
        "is_dog": False,
    },
]


def seed_data(db: Session) -> None:
    """幂等初始化：已存在的数据不覆盖。"""
    if not db.query(User).filter(User.username == "admin").first():
        db.add(
            User(
                username="admin",
                password_hash=hash_password("admin123"),
                nickname="图鉴管理员",
                role="admin",
            )
        )

    if not db.query(User).filter(User.username == "user").first():
        db.add(
            User(
                username="user",
                password_hash=hash_password("user123456"),
                nickname="小汪同学",
                role="user",
            )
        )

    for item in BREEDS:
        if not db.query(Breed).filter(Breed.slug == item["slug"]).first():
            db.add(Breed(**item))

    db.commit()