from models.category import SubCategoryItem


class Product:
    def __init__(self, title: str, webUrl: str, price: float, subCategoryItem: SubCategoryItem = None) -> None:
        self.title = title
        self.webUrl = webUrl
        self.price = price
        self.discounted_price = price
        self.subCategoryItem = subCategoryItem
        if self.subCategoryItem != None:
            self.sub_category_item_title = subCategoryItem.title
            self.sub_category_title = subCategoryItem.sub_category.title
            self.category_title = subCategoryItem.sub_category.category.title
        self.seller_count = 1
        self.avg_price = price
        self.min_price = price
        self.max_price = price
        self.avg_category_price = 0
        self.raiting_count = 0
        self.comment_count = 0
        self.favorite_count = 0
        self.basket_count = 0
        self.last24_hours_view_count = 0
        self.score = 0
        self.most_favorite = -1
        self.most_rated = -1
        self.best_seller = -1
        self.top_viewed = -1
        self.product_potential = 0