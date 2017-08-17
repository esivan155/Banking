# Authentication

Firstly, you'll need to create an authentication request to aquire an X Auth Token.  The headers are pulled from a request on my computer, feel free to change them to headers aquired from yours or another header.  Note that the URL is an encrypted HTTPS request, as are all calls made to the API.

    authenticate_request = requests.post(
        url="https://www.cibconline.cibc.com/ebm-anp/api/v1/json/sessions",
        json={"card": {"value": "{}".format(_username), "description": "", "encrypted": False, "encrypt": True},
              "password": "{}".format(_password)},
        headers={
            "Host": "www.cibconline.cibc.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0",
            "Accept": "application/vnd.api+json",
            "Accept-Language": "en",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer":"https://www.cibconline.cibc.com/ebm-resources/public/banking/cibc/client/web/index.html",
            "Content-Type": "application/vnd.api+json",
            "Client-Type": "default_web",
            "X-Auth-Token": "",
            "brand": "cibc",
            "WWW-Authenticate": "CardAndPassword",
            "X-Requested-With": "XMLHttpRequest",
            "Content-Length": "112",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache"
        }
    )

Next you'll need to save the cookies, responce header, and X Auth Token

    cookies = dict(authenticate_request.cookies)
    self.cookies = cookies
    authenticate_response_headers = authenticate_request.headers
    X_Auth_Token = authenticate_response_headers['X-Auth-Token']
    self.X_Auth_Token = X_Auth_Token

# Login Request

Make a login request like below.  Again the headers are not rigid, however, the "X-Auth-Token" filed must be the X Auth Token from earlier.

## request

    login_request = requests.get(
        url="https://www.cibconline.cibc.com/ebm-anp/api/v1/profile/json/userPreferences",
        headers={
            "Host": "www.cibconline.cibc.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0",
            "Accept": "application/vnd.api+json",
            "Accept-Language": "en",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer":"https://www.cibconline.cibc.com/ebm-resources/public/banking/cibc/client/web/index.html",
            "Content-Type": "application/vnd.api+json",
            "Client-Type": "default_web",
            "brand": "cibc",
            "X-Auth-Token": X_Auth_Token,
            "X-Requested-With": "XMLHttpRequest",
            "Connection": "keep-alive",
        },
        cookies=cookies
    )

## Account ID

after logging in as yourself, go ahead and pull your default account id from the responce

    login_request_response = login_request.json()
    defaultAccountId = login_request_response['userPreferences'][0]['payeePreferences'][0]['defaultAccountId']

your Default Account ID is persistant across sessions, however I don't recconmend saving it.

# Chequing Requests

Instead of going through the entire API, because I don't own it and didn't build it, i'll only go through pulling chequing account entries (credits and debits)

## url

    url = "https://www.cibconline.cibc.com/ebm-ai/api/v1/json/transactions?accountId={}&filterBy=range&fromDate={}&lastFilterBy=range&limit=250&lowerLimitAmount=&offset=0&sortAsc=true&sortByField=date&toDate={}&transactionLocation=&transactionType=&upperLimitAmount=".format(
            defaultAccountId,
            dateFrom.strftime("%Y-%m-%d"),
            dateUntil.strftime("%Y-%m-%d")
        )

the dateFrom and dateUntil arguments are python datetimes representing from when until when you want to pull credit and debit entries

## Request

    chequing_requests = requests.get(
        url="https://www.cibconline.cibc.com/ebm-ai/api/v1/json/transactions?accountId={}&filterBy=range&fromDate={}&lastFilterBy=range&limit=150&lowerLimitAmount=&offset=0&sortAsc=true&sortByField=date&toDate={}&transactionLocation=&transactionType=&upperLimitAmount=".format(
            defaultAccountId,
            dateFrom.strftime("%Y-%m-%d"),
            dateUntil.strftime("%Y-%m-%d")
        ),
        headers={
            "Host": "www.cibconline.cibc.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0",
            "Accept": "application/vnd.api+json",
            "Accept-Language": "en",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer":"https://www.cibconline.cibc.com/ebm-resources/public/banking/cibc/client/web/index.html",
            "Content-Type": "application/vnd.api+json",
            "Client-Type": "default_web",
            "brand": "cibc",
            "X-Auth-Token": X_Auth_Token,
            "X-Requested-With": "XMLHttpRequest",
            "Connection": "keep-alive",
        },
        cookies=cookies
      )
    transactions = chequing_requests.json()['transactions']

# Transactions

There are a couple of ways to do this one, I set it up as an iterator.  This is just to format the output as a nice dictionary.

    for transaction in transactions:
        transaction_type = 'Debit' if transaction['debit'] else 'Credit'
        date_datetime = datetime.datetime.strptime(transaction['date'].split('T')[0],"%Y-%m-%d")
        amount = transaction['debit'] if transaction_type == 'Debit' else transaction['credit']
        yield {
            'transaction': transaction_type,  # 'Debit' or 'Credit'
            'date': date_datetime,
            'details': transaction['transactionDescription'],
            'amount': amount,
            'balance': transaction['runningBalance']
        }