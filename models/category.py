class Category:
    def __init__(self, title, webUrl) -> None:
        self.title = title
        self.webUrl = webUrl



class SubCategory:
    def __init__(self, title, webUrl, category: Category) -> None:
        self.title = title
        self.webUrl = webUrl
        self.category = category



class SubCategoryItem:
    def __init__(self, title, webUrl, sub_category: SubCategory) -> None:
        self.title = title
        self.webUrl = webUrl
        self.sub_category = sub_category
        self.avg_category_price = 0