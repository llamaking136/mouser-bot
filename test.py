import requests, re

user_agent = "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0"

class Response:
    def __init__(self, url, is_valid, stock, in_stock):
        self.url = url
        self.is_valid = is_valid
        self.stock = stock
        self.in_stock = in_stock

    def __repr__(self):
        return f"Response(\"{self.url}\", {self.is_valid}, {self.stock}, {self.in_stock})"

def check_mouser_url(url):
    response = Response(url, None, None, False)
    request = requests.get(url, headers = {"User-Agent": user_agent})
    text = request.text
    split_text = text.split("\n")
    if not request.ok:
        return -request.status_code
    line_num = get_line(text, "class=\"panel-title pdp-pricing-header\"")
    if not line_num:
        response.is_valid = False
        return response

    response.is_valid = True

    line = split_text[line_num + 1].replace(",", "")
    if "Availability" in line:
        return response
    
    mat = re.search(r"In Stock: (\d+)", line)
    if not mat:
        return response
    stock = mat.group(0)

    response.in_stock = True
    response.stock = stock

    return response
    
    # split = text.split("\n")
    # return # strip(split[line]).strip()

def get_line(input_, text):
    split = input_.split("\n")
    for i in range(len(split)):
        if text in split[i]:
            return i
    return None

if __name__ == "__main__":
    print(check_mouser_url("https://www.mouser.com/ProductDetail/262-BMI088"))
