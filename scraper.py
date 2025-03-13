import requests
from bs4 import BeautifulSoup
import re
import json
import os 

from datetime import datetime
from pathlib import Path
import pickle

from models.category import Category, SubCategory, SubCategoryItem
from models.product import Product
import urllib.parse
import pandas as pd

class TYScraper:
    URL = "https://www.trendyol.com/"
    
    def __init__(self) -> None:
        self.data = pd.DataFrame(columns=['title', 'webUrl', 'price', 'discounted_price', 'sub_category_item_title', 'sub_category_title', 'category_title', 'seller_count', 'avg_price', 'min_price', 'max_price', 'avg_category_price', 'raiting_count', 'comment_count', 'favorite_count', 'basket_count', 'last24_hours_view_count', 'score', 'most_favorite', 'most_rated', 'best_seller', 'top_viewed', 'product_potential'])
        self.products = []
    
    def startCrawling(self, file_name: str, export_type: str = 'xlsx', product_count_each_category: int = 20, excluded_categories: list = []) -> None:
        request = requests.get(TYScraper.URL)
        source = BeautifulSoup(request.content, 'html.parser')
        scripts = source.find_all('script', {'type': 'application/javascript'})
        for script in scripts:
            if script.string and "window.__NAVIGATION_APP_INITIAL_STATE_V2__" in script.string:
                match = re.search(r'window\.__NAVIGATION_APP_INITIAL_STATE_V2__\s*=\s*(\{.*\});', script.string, re.DOTALL)
                if match:
                    categories_json = json.loads(match.group(1))
                    break
                
        
        TYScraper.writeJSON(categories_json, 'categories', f'/categories.json')
        
        
        sub_category_items: list = []
        for category in categories_json["items"]:
            new_category = Category(category["title"].strip().replace('&', '').replace(' ', '-'), category["webUrl"])
            for sub_category in category["children"]:
                try:
                    new_sub_category = SubCategory(sub_category["title"].strip().replace('&', '').replace(' ', '-'), sub_category["webUrl"], new_category)
                    if "children" in sub_category:
                        for sub_category_item in sub_category["children"]:
                            new_sub_category_item = SubCategoryItem(sub_category_item["title"].strip().replace('&', '').replace(' ', '-'), sub_category_item["webUrl"], new_sub_category)
                            sub_category_items.append(new_sub_category_item)
                except Exception as ex:
                    print(ex, sub_category)
        counter = 0
        for sub_category_item in sub_category_items:
            try:
                if counter > 0:
                    file_path = f"./checkpoints/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
                    self.exportProductsToExcel(file_path)
                    self.pickle_products()
                self.scrapCategory(sub_category_item)
                counter += 1
            except Exception as err:
                print('Error while scraping category', sub_category_item.webUrl, 'Error:', err)
        
        self.exportProductsToExcel(file_name)
        
        
    def scrapCategory(self, subCategoryItem: SubCategoryItem) -> None:
        target_url = urllib.parse.urljoin(TYScraper.URL, subCategoryItem.webUrl)
        print(target_url, 'category is scraping...')
        request = requests.get(target_url)
        source = BeautifulSoup(request.content, 'html.parser')
        
        scripts = source.find_all('script', {'type': 'application/javascript'})
        for script in scripts:
            if script.string and "window.__SEARCH_APP_INITIAL_STATE__" in script.string:
                match = re.search(r'window.__SEARCH_APP_INITIAL_STATE__\s*=\s*(\{.*\});', script.string, re.DOTALL)
                if match:
                    products_json = json.loads(match.group(1))
                    break
                
        TYScraper.writeJSON(products_json, f'{subCategoryItem.sub_category.category.title}/{subCategoryItem.sub_category.title}', f'{subCategoryItem.webUrl}.json')
        
        products = [Product(product['name'], product['url'], product['variants'][0]['price']['sellingPrice'], subCategoryItem) for product in products_json['products']]
        category_price_avg = sum([pr.price for pr in products]) / len(products)
        subCategoryItem.avg_category_price = category_price_avg
        
        for product in products:
            try:
                self.scrapProduct(product)
            except Exception as err:
                print('Error while scraping product', product.webUrl, 'Error:', err)
            
    def scrapProduct(self, product: Product) -> None:
        target_url = urllib.parse.urljoin(TYScraper.URL, product.webUrl)
        print(target_url, 'product is scraping...')
        
        request = requests.get(target_url)
        source = BeautifulSoup(request.content, 'html.parser')
        
        scripts = source.find_all('script', {'type': 'application/javascript'})
        for script in scripts:
            if script.string and "window.__PRODUCT_DETAIL_APP_INITIAL_STATE__" in script.string:
                match = re.search(r'window\.__PRODUCT_DETAIL_APP_INITIAL_STATE__\s*=\s*(\{.*\});', script.string, re.DOTALL)
                if match:
                    pr_data_json = json.loads(match.group(1))
                    break
                        
        TYScraper.writeJSON(pr_data_json, f'{product.subCategoryItem.sub_category.category.title}/{product.subCategoryItem.sub_category.title}/{product.subCategoryItem.title}', f'{product.webUrl}.json')
        
        product.discounted_price = pr_data_json['product']['variants'][0]['price']['discountedPrice']['value']
        other_merchants = pr_data_json['product']['otherMerchants']
        if len(other_merchants) > 0:
            product.seller_count += len(other_merchants)
            product.min_price = min([om['price']['sellingPrice'] if isinstance(om['price']['sellingPrice'], int) else om['price']['sellingPrice']['value'] for om in other_merchants] + [product.discounted_price])
            product.max_price = max([om['price']['sellingPrice'] if isinstance(om['price']['sellingPrice'], int) else om['price']['sellingPrice']['value'] for om in other_merchants] + [product.discounted_price])
            product.avg_price = (sum([om['price']['sellingPrice'] if isinstance(om['price']['sellingPrice'], int) else om['price']['sellingPrice']['value'] for om in other_merchants]) + product.price) / (len(other_merchants) + 1)
            
        if (product.subCategoryItem != None):
            product.avg_category_price = product.subCategoryItem.avg_category_price
            
        product.comment_count = pr_data_json['product']['ratingScore']['totalCommentCount']
        product.raiting_count = pr_data_json['product']['ratingScore']['totalRatingCount']
        product.score = pr_data_json['product']['ratingScore']['averageRating']
        product.favorite_count = pr_data_json['product']['favoriteCount']
        
        if 'basketCount' in pr_data_json['product']['socialProof']:
            product.basket_count = TYScraper.formatTyNumber(pr_data_json['product']['socialProof']['basketCount'])
        
        if 'pageViewCount' in pr_data_json['product']['socialProof']:
            product.last24_hours_view_count = TYScraper.formatTyNumber(pr_data_json['product']['socialProof']['pageViewCount'])
        
        if (pr_data_json['product']['categoryTopRankings'] != None):
            if (pr_data_json['product']['categoryTopRankings']['name'] == 'bestSeller'):
                product.best_seller = pr_data_json['product']['categoryTopRankings']['order']
                
            if (pr_data_json['product']['categoryTopRankings']['name'] == 'mostFavourite'):
                product.most_favorite = pr_data_json['product']['categoryTopRankings']['order']
                
            if (pr_data_json['product']['categoryTopRankings']['name'] == 'mostRated'):
                product.most_rated = pr_data_json['product']['categoryTopRankings']['order']
                
            if (pr_data_json['product']['categoryTopRankings']['name'] == 'topViewed'):
                product.top_viewed = pr_data_json['product']['categoryTopRankings']['order']
        
        product.product_potential = (1 / product.seller_count) * (product.comment_count / (product.favorite_count if product.favorite_count > 0 else 1)) * ((product.score ** 2) * product.raiting_count)
        
        self.insertProductData(product)
        self.products.append(product)
        
    def insertProductData(self, product: Product) -> None:
        pr_dict = vars(product)
        pr_dict.pop('subCategoryItem')
        self.data = self.data._append(pr_dict, ignore_index = True)
        
    def exportProductsToExcel(self, fileName: str) -> None:
        try:
            target_path = './' + str(Path(fileName).parent)
            if not os.path.exists(target_path):
                os.makedirs(target_path)
            self.data.to_excel(fileName, index=False)
            print('file saved to', fileName)
        except Exception as err:
            print('Unhandled exception while file saving...', fileName, 'Error:', err)
        
    def pickle_products(self) -> None:
        if not os.path.exists('./pickles'):
            os.makedirs('./pickles')

        with open('./pickles/products.pkl', 'wb') as f:
            pickle.dump(self.products, f)
        
    @staticmethod
    def writeJSON(content: str, path, file_name) -> None:
        try:
            path = f'./scraped_pages/{path}'
            target_file = path + file_name
            
            target_path = './' + str(Path(target_file).parent)
            if not os.path.exists(target_path):
                os.makedirs(target_path)

            with open(target_file, 'w', encoding='utf-8') as file:
                file.write(json.dumps(content, indent=4))
        except Exception as err:
            print('Exception while writing json file', target_file, 'Error:', err)
            
    @staticmethod
    def formatTyNumber(number: str) -> int:
        return int(float(number.replace('B', '').replace('.', '')) * 100) if 'B' in number else int(number.replace('.', ''))
    
    