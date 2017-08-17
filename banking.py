import os
import requests
import datetime
import re

# if you don't want to put these in every time, feel free to hard code these in.
_username = None
_password = None

# pull data from CIBC API and format it
class Parse():
    def __init__(self,
                 dateFrom = datetime.datetime(2017,5,1),
                 dateUntil = datetime.datetime(2017,8,20),
                 X_Auth_Token=None,
                 cookies=None,
                 file=None):
        global _username
        global _password
        if not _username:
            _username = input("Bank Account Number: ")
        if not _password:
            _password = input("Bank Account Password: ")
        self.dateUntil = dateUntil
        self.dateFrom = dateFrom
        self.transactions = self.aquireTransactions(dateFrom,dateUntil)
        self.tr_clean = self.removeRepeats()

    # get the credits/debits since datefrom until dateuntil.  If X_auth_token and cookies are provided, will not re authenticate
    # but use the existing X auth Token and cookies provided
    def aquireTransactions(self,dateFrom,dateUntil, X_Auth_Token=None, cookies=None):
        if not (X_Auth_Token and cookies):
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
                    "Referer": "https://www.cibconline.cibc.com/ebm-resources/public/banking/cibc/client/web/index.html",
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
            cookies = dict(authenticate_request.cookies)
            self.cookies = cookies
            authenticate_response_headers = authenticate_request.headers
            X_Auth_Token = authenticate_response_headers['X-Auth-Token']
            self.X_Auth_Token = X_Auth_Token
        login_request = requests.get(
            url="https://www.cibconline.cibc.com/ebm-anp/api/v1/profile/json/userPreferences",
            headers={
                "Host": "www.cibconline.cibc.com",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0",
                "Accept": "application/vnd.api+json",
                "Accept-Language": "en",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://www.cibconline.cibc.com/ebm-resources/public/banking/cibc/client/web/index.html",
                "Content-Type": "application/vnd.api+json",
                "Client-Type": "default_web",
                "brand": "cibc",
                "X-Auth-Token": X_Auth_Token,
                "X-Requested-With": "XMLHttpRequest",
                "Connection": "keep-alive",
            },
            cookies=cookies
        )
        print(dateFrom.strftime("%Y-%m-%d"),
                dateUntil.strftime("%Y-%m-%d"))
        login_request_response = login_request.json()
        defaultAccountId = login_request_response['userPreferences'][0]['payeePreferences'][0]['defaultAccountId']
        url = "https://www.cibconline.cibc.com/ebm-ai/api/v1/json/transactions?accountId={}&filterBy=range&fromDate={}&lastFilterBy=range&limit=250&lowerLimitAmount=&offset=0&sortAsc=true&sortByField=date&toDate={}&transactionLocation=&transactionType=&upperLimitAmount=".format(
                defaultAccountId,
                dateFrom.strftime("%Y-%m-%d"),
                dateUntil.strftime("%Y-%m-%d")
            )
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
                "Referer": "https://www.cibconline.cibc.com/ebm-resources/public/banking/cibc/client/web/index.html",
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

    # If an amount if both credited and debited, that amount is removed from our consideration.
    def removeRepeats(self):
        transaction = list(self.transactions)
        Credits = list(filter(lambda x: x['transaction'] == 'Credit',transaction))
        Debits = list(filter(lambda x: x['transaction'] == 'Debit',transaction))
        DebitPool = [ele['amount'] for ele in Debits]
        CreditPool = [ele['amount'] for ele in Credits]
        properDebits = list(filter(lambda x: x['amount'] not in CreditPool,Debits))
        properCredits = list(filter(lambda x: x['amount'] not in DebitPool, Credits))
        return properCredits + properDebits

class Build():
    def __init__(self):
        # lets clear out customInsertion.js
        fileDir = os.path.dirname(os.path.abspath(__file__))
        jsdir = os.path.join(os.path.join(fileDir,'bankTemplate'),'js')
        f =  open(os.path.join(jsdir,'customInsertion.js'), 'w+')
        f.write('')
        f.close()
        self.createChart = False # indicates if the createchart function has already been built

    def nominalTable(self,normal_table,currDate):
        fileDir = os.path.dirname(os.path.abspath(__file__))
        jsdir = os.path.join(os.path.join(fileDir,'bankTemplate'),'js')
        with open(os.path.join(jsdir,'customInsertion.js'), 'a') as jsfile:
            html = 'html = `<table id="Nominal-Weekly-Distribution" class="display" cellspacing="0" width="100%">\n'
            html += "\n".join([
                "  <thead>",
                "      <tr>",
                "          <th>Week</th>",
                "          <th>Week Income</th>",
                "          <th>Week Income After Bills</th>",
                "          <th>Debit</th>",
                "          <th>Week Net</th>",
                "          <th>Debt/Surplus</th>",
                "      </tr>",
                "  </thead>",
                "  <tfoot>",
                "      <tr>",
                "          <th>Week</th>",
                "          <th>Week Income</th>",
                "          <th>Week Income After Bills</th>",
                "          <th>Debit</th>",
                "          <th>Week Net</th>",
                "          <th>Debt/Surplus</th>",
                "      </tr>",
                "  </tfoot>",
                "  <tbody>\n"
            ])
            for entry in normal_table:
                if entry['dates'][0] > currDate:
                    dateColor = "grey"
                else:
                    dateColor = "black"
                if entry['Deficit'] >= 0:
                    Deficit_color = 'green'
                    Deficit = entry['Deficit']
                else:
                    Deficit_color = 'red'
                    Deficit = (-1)*entry['Deficit']
                if entry['Debt'] >= 0:
                    Debt_color = 'green'
                    Debt = entry['Debt']
                else:
                    Debt_color = 'red'
                    Debt = (-1) * entry['Debt']
                html += "\n".join([
                    "      <tr>",
                    '          <td style="color:{};">{}</td>'.format(dateColor,entry['dates'][0].strftime("%b %d, %Y")),
                    '          <td style="color:green;">${}</td>'.format(entry['income']),
                    '          <td style="color:#008055;">${}</td>'.format(entry['income_ab']),
                    '          <td style="color:red;">${}</td>'.format(entry['Debit']),
                    '          <td style="color:{};">${}</td>'.format(Deficit_color,Deficit),
                    '          <td style="color:{};">${}</td>'.format(Debt_color,Debt),
                    '      </tr>\n'
                ])
            html += "  </tbody>\n</table>\n`\n"
            html += "$('#Nominal-Weekly-Distribution-wrapper').html(html);\n"
            html += "$('#Date').html('{}');\n".format(currDate.strftime('%b %d, %Y'))
            jsfile.write(html)

    # graphs the running balance, weekly expenditure, income_ab, and income of a given term
    # creates an id and data labels based on chart num
    # ids in the HTML must be added manually.
    def BalanceBurndown(self,balance,income,income_ab,expenditure, chartnum):
        fileDir = os.path.dirname(os.path.abspath(__file__))
        jsdir = os.path.join(os.path.join(fileDir, 'bankTemplate'), 'js')
        with open(os.path.join(jsdir, 'customInsertion.js'), 'a') as jsfile:
            jsfile.write('\n')
            htmlCreateChart ='''
function createChart(seriesOptions, id) {

    Highcharts.stockChart(id, {

        legend: {
            enabled: true,
            align: 'right',
            backgroundColor: '#FCFFC5',
            borderColor: 'black',
            borderWidth: 2,
            layout: 'vertical',
            verticalAlign: 'top',
            y: 100,
            shadow: true
        },

        rangeSelector: {
            selected: 4
        },

        yAxis: {
            labels: {
                formatter: function () {
                    return '$' + this.value
                }
            },
            plotLines: [{
                value: 0,
                width: 2,
                color: 'silver'
            }]
        },

        xAxis: {
            type: 'datetime'
        },

        plotOptions: {
            series: {
                showInNavigator: true
            }
        },

        tooltip: {
            pointFormat: '<span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> ({point.change}%)<br/>',
            valueDecimals: 2,
            split: true
        },

        series: seriesOptions
    });
}
        '''
            if not self.createChart:
                jsfile.write(htmlCreateChart)
                jsfile.write('\n\n')
                self.createChart = True
            seriesOptions = [
                {
                    'name':'Balance',
                    'data':balance
                },
                {
                    'name': 'Income',
                    'data': income
                },
                {
                    'name': 'Income After Bills',
                    'data': income_ab
                },
                {
                    'name': 'Expenditure',
                    'data': expenditure
                }
            ]
            htmlSeriesOptions = str(seriesOptions)
            jsfile.write('\n')
            jsfile.write('seriesOptions{} = {}\n'.format(chartnum,htmlSeriesOptions))
            jsfile.write('createChart(seriesOptions{0},"BalanceBurndown{0}")'.format(chartnum))
            jsfile.write('\n')

    def ANOE(self, seriesOptions):
        fileDir = os.path.dirname(os.path.abspath(__file__))
        jsdir = os.path.join(os.path.join(fileDir, 'bankTemplate'), 'js')
        with open(os.path.join(jsdir, 'customInsertion.js'), 'a') as jsfile:
            jsfile.write('\n')
            htmlCreateChart = '''
        function createChartANOE(seriesOptions, id) {

            Highcharts.stockChart(id, {

                legend: {
                    enabled: true,
                    align: 'right',
                    backgroundColor: '#FCFFC5',
                    borderColor: 'black',
                    borderWidth: 2,
                    layout: 'vertical',
                    verticalAlign: 'top',
                    y: 100,
                    shadow: true
                },

                rangeSelector: {
                    selected: 4
                },

                yAxis: {
                    labels: {
                        formatter: function () {
                            return '$' + this.value
                        }
                    },
                    plotLines: [{
                        value: 0,
                        width: 2,
                        color: 'silver'
                    }]
                },
                plotOptions: {
                    series: {
                        showInNavigator: true
                    }
                },

                tooltip: {
                    pointFormat: '<span style="color:{series.color}">{series.name}</span>: <b>{point.y}</b> ({point.change}%)<br/>',
                    valueDecimals: 2,
                    split: true
                },

                series: seriesOptions
            });
        }
                '''
            if not self.createChartANOE:
                jsfile.write(htmlCreateChart)
                jsfile.write('\n\n')
                self.createChartANOE = True
            htmlSeriesOptions = str(seriesOptions)
            jsfile.write('\n')
            jsfile.write('seriesOptionsANOE = {}\n'.format(htmlSeriesOptions))
            jsfile.write('createChartANOE(seriesOptionsANOE,"ANOE")')
            jsfile.write('\n')

class StudentBanking(Parse, Build):
    def __init__(self, MonthlyExpenses, realExclusion, extra=None):
        super(StudentBanking,self).__init__()
        # we can use the cookies and auth token from the orignonal log in to emulate subsiquent log ins,
        # without re entering card and password data
        Build.__init__(self)
        # Parse.__init__(self)
        # amount we don't include in analysis.  Rent, tuition.
        self.realExclusion = realExclusion
        # monthly bills, used to find income after bills expense
        self.MonthlyExpenses = MonthlyExpenses
        # transactions, after repeats - Debits and credits of the same amount, and exclusions
        self.tr_clean = self.adjustTransactions()
        # date of most recent transaction in calculation
        self.currDate = sorted([ele for ele in self.tr_clean], key=lambda x: x['date'])[-1]['date']
        self.initial = self.initialMoney()
        self.normal_weekly_income,self.normal_weekly_income_ab, self.normal_table = self.weeklyTableNominal()
        self.dates = dates = [self.unix_time_millis(ele['dates'][0]) for ele in self.normal_table]
        # used to compare with weekly expednditures of other terms
        self.weekly_expenditure = [list(ele) for ele in sorted(list(zip(self.dates, [ele['Debit'] for ele in self.normal_table])), key=lambda x: x[0])]
        Build.nominalTable(self,self.normal_table,self.currDate) # build the nominal table in the JS,HTML
        # creates financial chart for previous terms
        burndown, income, income_ab, weekly_expenditure_now = self.balanceBurndown(
            dateFrom=self.dateFrom,
            dateUntil=self.dateUntil,
            MonthlyExpenses=self.MonthlyExpenses,
            customExclusions=self.realExclusion
        )
        Build.BalanceBurndown(self, burndown, income, income_ab, weekly_expenditure_now, 4)
        weekly_expenditure_list = [
            {
                'name': 'Spring 2017',
                'data': [list(ele) for ele in zip(range(len(weekly_expenditure_now) + 1)[1:], [ele[1] for ele in weekly_expenditure_now])]
            }
        ]
        chartno = 0
        self.createChartANOE = False
        for data in extra:
            chartno += 1
            name = data.pop('name')
            burndown, income, income_ab, weekly_expenditure = self.balanceBurndown(**data)
            weekly_expenditure_list.append({
                'name': name,
                'data': [list(ele) for ele in zip(range(len(weekly_expenditure) + 1)[1:], [ele[1] for ele in weekly_expenditure])]
            })
            Build.BalanceBurndown(self,burndown, income, income_ab, weekly_expenditure, chartno)
            if chartno == 3:
                # max 3 charts + current chart.  for more, add custom HTML editor to add block for chart dynamically
                break

        # analysis of expenditures table
        Build.ANOE(self,weekly_expenditure_list)

    # sort out the real exclusions from the list of transactions
    def Exclusions(self, transaction, exclusions=None):
        if not exclusions:
            for Exc in self.realExclusion.values():
                if(re.match(Exc[0],transaction['details'])):
                    return False
            return True
        else:
            for Exc in exclusions.values():
                if(re.match(Exc[0],transaction['details'])):
                    return False
            return True

    # adjusts the transactions
    def adjustTransactions(self, customExclusions = None, tr_clean=None):
        tr_clean = tr_clean if tr_clean else self.tr_clean
        customExclusions = customExclusions if customExclusions else self.realExclusion
        Credits = list(filter(lambda x: x['transaction'] == 'Credit', tr_clean))
        Debits = list(filter(lambda x: x['transaction'] == 'Debit', tr_clean))
        if customExclusions:
            new_Debits = list(filter(lambda x: self.Exclusions(x, customExclusions), Debits))
            new_Credits = list(filter(lambda x: self.Exclusions(x, customExclusions), Credits))
        else:
            new_Debits = list(filter(self.Exclusions, Debits))
            new_Credits = list(filter(self.Exclusions, Credits))
        return new_Debits + new_Credits

    # O(nm) n = number of debits, m = number of credits
    # may use custom realExclusion
    def initialMoney(self, realExclusion=None, tr_clean=None, dateFrom = None, dateUntil = None):
        tr_clean = tr_clean if tr_clean else self.tr_clean
        dateFrom = dateFrom if dateFrom else self.dateFrom
        dateUntil = dateUntil if dateUntil else self.dateUntil
        realExclusion = realExclusion if realExclusion else self.realExclusion
        total = 0
        Credits = filter(lambda x: x['transaction'] == 'Credit', tr_clean)
        Debits = filter(lambda x: x['transaction'] == 'Debit', tr_clean)
        for credit in Credits:
            intersection = filter(lambda x: x['amount'] == credit['amount'], Debits)
            if len(list(intersection)) == 0:
                total += credit['amount']
        # we need to add the initial balance
        total += sorted([ele for ele in tr_clean],key=lambda x: x['date'])[0]['balance']
        # remove real exclusion items
        DebitExlusion = list(filter(lambda x: x[3] == 'Debit', realExclusion.values()))
        CreditExlusion = list(filter(lambda x: x[3] == 'Credit', realExclusion.values()))
        def Exclusions(Exlusion, type):
            total_weeks = self.weeksSince(dateFrom, dateUntil)
            etotal = 0.0
            for exc in Exlusion:
                etotal -= (exc[1]*exc[2] if type == 'Debit' else -exc[1]*exc[2])
            return etotal
        total += Exclusions(DebitExlusion,'Debit') + Exclusions(CreditExlusion,'Credit')
        return total

    # takes start and end dates and interval.  Produces list of times spanning interval from the start to the end date.
    # returns date generator.  For list, simply return list of elements instead
    def dateTimeLine(self,startDate, endDate, interval=datetime.timedelta(days=7)):
        while startDate < endDate:
            yield [startDate,startDate + interval - datetime.timedelta(days=1)]
            startDate = startDate + interval

    # counts the number of weeks between startDate and currentDate.  currentDate must be larger
    def weeksSince(self,startDate, currentDate, interval = datetime.timedelta(days=7)):
        count = 0
        while currentDate > startDate:
            currentDate = currentDate - interval
            count += 1
        return count

    # returns the amount of money spent within the given dates
    def accountAccumulation(self, fromDate, untilDate, tr_clean=None):
        tr_clean = tr_clean if tr_clean else self.tr_clean
        properDebit = list(filter(lambda x: x['transaction'] == 'Debit',tr_clean))
        rangedDebit = list(filter(lambda x: x['date'] >= fromDate and x['date'] <= untilDate, properDebit))
        return sum([ele['amount'] for ele in rangedDebit])

    # returns weekly table values not exluding any values.
    def weeklyTableNominal(self, tr_clean=None, dateFrom=None, dateUntil=None, currDate=None, initial=None, MonthlyExpenses=None):
        tr_clean = tr_clean if tr_clean else self.tr_clean
        print(len(sorted(tr_clean, key=lambda x: x['date'])))
        dateFrom = dateFrom if dateFrom else self.dateFrom
        dateUntil = dateUntil if dateUntil else self.dateUntil
        currDate = currDate if currDate else self.currDate
        initial = initial if initial else self.initial
        MonthlyExpenses = MonthlyExpenses if MonthlyExpenses else self.MonthlyExpenses

        interval = datetime.timedelta(days=7)
        intervals = self.dateTimeLine(dateFrom, dateUntil, interval)
        intervals = sorted(intervals, key=lambda x: x[0])
        total_weeks = self.weeksSince(dateFrom, dateUntil,interval)
        bill_expenditure_weekly = sum(MonthlyExpenses.values())/4.0
        weekly_income = initial / total_weeks
        weekly_income_ab = weekly_income - bill_expenditure_weekly # after bills, and one time expenditures
        table = []
        debt = 0
        for inter in intervals:
            if inter[0] < currDate + datetime.timedelta(days=7):
                # if we are projecting into the future, the income calc. from most recent income calculation is used
                income = (initial - self.accountAccumulation(dateFrom,inter[0]-datetime.timedelta(days=1), tr_clean=tr_clean)) / (total_weeks - self.weeksSince(dateFrom, inter[0]))
            debit = self.accountAccumulation(inter[0], inter[1], tr_clean=tr_clean) if self.accountAccumulation(inter[0],inter[1], tr_clean=tr_clean) != 0 else bill_expenditure_weekly
            debt = debt + income - debit
            income_ab = income - bill_expenditure_weekly
            table.append(
                {
                    'dates': inter,
                    'income': round(income, 2),
                    'Debit': round(debit, 2),
                    'Deficit': round(income - debit, 2),
                    'Debt': round(debt, 2),
                    'income_ab': round(income_ab, 2)
                }
            )
        return weekly_income,weekly_income_ab,table

    def unix_time_millis(self,dt):
        epoch = datetime.datetime.utcfromtimestamp(0)
        return int((dt - epoch).total_seconds() * 1000)

    # produces the running balance, weekly expenditure, and income of a given time interval
    ## IMPORTANT THIS WILL RESET IMPORTANT CLASS VARIABLES
    def balanceBurndown(self, dateFrom, dateUntil,customExclusions,MonthlyExpenses):
        # can't handle more then 141 transactions in one request, we spplit into 2 request and add them
        if self.weeksSince(startDate=dateFrom,currentDate=dateUntil) > 5:
            interDate = dateFrom + datetime.timedelta(weeks=5)
            p1 = Parse(dateFrom,interDate,X_Auth_Token=self.X_Auth_Token,cookies=self.cookies)
            p2 = Parse(interDate, dateUntil, X_Auth_Token=self.X_Auth_Token, cookies=self.cookies)
            tr_clean = self.adjustTransactions(customExclusions, tr_clean=p1.tr_clean + p2.tr_clean)
        else:
            p = Parse(dateFrom,dateUntil,X_Auth_Token=self.X_Auth_Token,cookies=self.cookies)
            tr_clean = self.adjustTransactions(customExclusions, tr_clean=p.tr_clean)
        currDate = sorted([ele for ele in tr_clean], key=lambda x: x['date'])[-1]['date']
        initial = self.initialMoney(realExclusion=customExclusions, tr_clean=tr_clean,dateUntil=dateUntil,dateFrom=dateFrom)
        burndown = initial
        # Lets get all the table data
        table = self.weeklyTableNominal(tr_clean=tr_clean, dateFrom=dateFrom, dateUntil=dateUntil, currDate=currDate, initial=initial, MonthlyExpenses=MonthlyExpenses)[-1]
        # graphs the running balance, weekly expenditure, income_ab, and income of a given term
        dates = [self.unix_time_millis(ele['dates'][0]) for ele in table] # first date in interval
        income = [list(ele) for ele in sorted(list(zip(dates,[ele['income'] for ele in table])), key=lambda x: x[0])]
        weekly_expenditure = [list(ele) for ele in sorted(list(zip(dates,[ele['Debit'] for ele in table])), key=lambda x: x[0])]
        income_ab = [list(ele) for ele in sorted(list(zip(dates, [ele['income_ab'] for ele in table])), key=lambda x:x[0])]
        burndown_list = []
        for ele in table:
            burndown_list.append(burndown-ele['Debit'])
            burndown = burndown - ele['Debit']
        burndown = [list(ele) for ele in sorted(list(zip(dates,burndown_list)), key=lambda x: x[0])]
        return burndown, income, income_ab, weekly_expenditure

if __name__ == '__main__':

    MonthlyExpenses={
            'laundry': 20,
            'groceries': 130,
            'phone': 40,
            'hydro': 60
    }

    B = StudentBanking(
        MonthlyExpenses=MonthlyExpenses,
        realExclusion={
            'rent': [re.compile(r'PREAUTHORIZED DEBIT .* KW4RENT INC'),625, 2, 'Debit'],
                                r'PREAUTHORIZED DEBIT .* KW4RENT INC'
            'tuition': [re.compile(r'INTERNET BILL PAY .* UNIVERSITY OF WATERLOO'),3224.89,1,'Debit']
        },
        extra=[
            {
                'name': 'Fall 2016',
                'dateFrom':datetime.datetime(year=2016,month=9,day=1),
                'dateUntil':datetime.datetime(year=2016,month=12,day=20),
                'MonthlyExpenses':MonthlyExpenses,
                'customExclusions':{
                        'rent': [re.compile(r'PREAUTHORIZED DEBIT .* KW4RENT INC'), 625, 4, 'Debit'],
                        'tuition': [re.compile(r'INTERNET BILL PAY .* UNIVERSITY OF WATERLOO'),2550.25, 1, 'Debit']
                }
            },
            {
                'name': 'Spring, 2016',
                'dateFrom':datetime.datetime(year=2016,month=5,day=1),
                'dateUntil':datetime.datetime(year=2016,month=8,day=20),
                'MonthlyExpenses':MonthlyExpenses,
                'customExclusions':{
                    'rent': [re.compile(r'PREAUTHORIZED DEBIT .* KW4RENT INC'), 625, 4, 'Debit'],
                    'tuition': [re.compile(r'INTERNET BILL PAY .* UNIVERSITY OF WATERLOO'),2445.19, 1, 'Debit']
                }
            },
            {
                'name': 'Winter, 2015',
                'dateFrom':datetime.datetime(year=2015,month=1,day=1),
                'dateUntil':datetime.datetime(year=2015,month=4,day=20),
                'MonthlyExpenses':MonthlyExpenses,
                'customExclusions':{
                    'rent': [re.compile(r'.* ZAIN VALANI'), 560, 3, 'Debit'],
                    'tuition': [re.compile(r'INTERNET BILL PAY .* UNIVERSITY OF WATERLOO'), 1049.0, 1, 'Debit']
                }
            },
        ]
    )