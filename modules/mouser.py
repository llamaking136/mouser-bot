import requests, re, json
import modules.email_m as email

user_agent = "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0"
api_url = "https://api.mouser.com/api/v1/"    

def check_mouser_part(apikey, partnum, error_email = True):
    """ # using old method, screen scraper
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
    """ # using new method, mouser api
    response = requests.post(api_url + f"search/partnumber?apikey={apikey}", json = {
        "SearchByPartRequest": {
            "mouserPartNumber": partnum
        }
    }, headers = {'Content-Type': 'application/json'})

    if not response.ok:
        return -response.status_code

    res_json = response.json()

    if len(res_json["Errors"]) >= 1 and error_email:
        email.send_error_email("Errors during API call!", debug = {"Errors": res_json["Errors"]})
        return None

    if res_json["SearchResults"]["NumberOfResult"] > 1:
        return -2

    raw_stock = res_json["SearchResults"]["Parts"][0]["Availability"]

    if "On Order" in raw_stock:
        return -1

    stock = int(raw_stock.replace(" In Stock", ""))

    return stock

def get_line(input_, text):
    split = input_.split("\n")
    for i in range(len(split)):
        if text in split[i]:
            return i
    return None

if __name__ == "__main__":
    response = check_mouser_product("262-BMI088")

    print(response)
