class Asset:
    def __init__(self, name, property_dict):
        self.name = name
        self.property_dict = property_dict
        # update portfolio of agents
        for agent, quantity in self.property_dict.items():
            agent.portfolio.update({self: quantity})

    def __str__(self):
        return self.name

    def print_state(self):
        print('Asset: ' + str(self.name))
        print('     Property Dictionary:')
        for agent, quantity in self.property_dict.items():
            print('         {0}: {1}'.format(agent.name, quantity))


class Money(Asset):
    pass


class Market:
    def __init__(self, name, assets, assets_money):
        self.name = name
        self.order_books = dict()
        for asset, asset_money in zip(assets, assets_money):
            self.order_books.update({(asset, asset_money): OrderBook(asset, asset_money)})

    def acknowledge_place_order(self, order):
        """
        :return:
            True if order placed
            False if order not placed
        """
        try:
            if (order.asset, order.asset_money) in self.order_books:
                self.order_books[(order.asset, order.asset_money)].add_order(order)
            return True
        except:
            Warning('Order not placed')
            return False

    def acknowledge_cancel_order(self, order):
        """
        :return:
            True if order canceled
            False if order not canceled
        """
        try:
            if (order.asset, order.asset_money) in self.order_books:
                self.order_books[(order.asset, order.asset_money)].delete_order(order)
            return True
        except:
            Warning('Order not canceled')
            return False

    def match_orders(self):
        pass

    def print_order_books(self):
        for key, order_book in self.order_books.items():
            print(order_book)


class OrderBook:
    def __init__(self, asset, asset_money):
        self.asset = asset
        self.asset_money = asset_money
        self.buy_orders = list()
        self.sell_orders = list()

    def __str__(self):
        string = 'Order Book --> Asset: ' + str(self.asset) + ', Money Asset: ' + str(self.asset_money) + '\n'
        string += '     Buy Orders'
        for order in self.buy_orders:
            string += '\n' + order.__str__()
        string += '\n     Sell Orders'
        for order in self.sell_orders:
            string += '\n' + order.__str__()
        return string

    def add_order(self, order):
        if order.buysell:  # BUY ORDER
            inserted = False
            for i in range(0, len(self.buy_orders)):
                if order.price < self.buy_orders[i].price:
                    self.buy_orders.insert(i, order)
                    inserted = True
                    break
            if not inserted:
                self.buy_orders.append(order)
        else:  # SELL ORDER
            inserted = False
            for i in range(0, len(self.sell_orders)):
                if order.price > self.sell_orders[i].price:
                    self.sell_orders.insert(i, order)
                    inserted = True
                    break
            if not inserted:
                self.sell_orders.append(order)

    def delete_order(self, order):
        try:
            if order.buysell:
                self.buy_orders.remove(order)
            else:
                self.sell_orders.remove(order)
        except ValueError:
            Warning('Order was not in Order Book')

    def match_orders(self):
        pairings = list()  # paring => (buy_order, sell_order, executionprice = avg(buy_price, sell_price))
        while self.buy_orders[0].price >= self.sell_orders[0].price:
            buy_order = self.buy_orders[0]
            sell_order = self.sell_orders[0]
            if buy_order.quantity == sell_order.quantity:
                self.buy_orders.remove(buy_order)
                self.sell_orders.remove(sell_order)
                buy_order.agent.orders[buy_order.asset].remove(buy_order)
                sell_order.agent.orders[sell_order.asset].remove(sell_order)
                pairings.append((buy_order, sell_order,
                                 (buy_order.price + sell_order.price) / 2))
            elif buy_order.quantity > sell_order.quantity:  # more buying than selling
                self.buy_orders.remove(buy_order)
                self.sell_orders.remove(sell_order)
                buy_order.agent.orders[buy_order.asset].remove(buy_order)
                sell_order.agent.orders[sell_order.asset].remove(sell_order)
                new_buy_order = Order(True, buy_order.quantity - sell_order.quantity, buy_order.asset, buy_order.price,
                                      buy_order.asset_money, buy_order.agent)
                buy_order.agent.orders[buy_order.asset].append(new_buy_order)
                assigned_buy_order = Order(True, sell_order.quantity, buy_order.asset, buy_order.price,
                                           buy_order.asset_money, buy_order.agent)
                self.buy_orders.insert(0, new_buy_order)
                pairings.append((assigned_buy_order, sell_order, (assigned_buy_order.price + sell_order.price) / 2))
            elif sell_order.quantity < buy_order.quantity:  # more selling than buying
                self.buy_orders.remove(buy_order)
                self.sell_orders.remove(sell_order)
                buy_order.agent.orders[buy_order.asset].remove(buy_order)
                sell_order.agent.orders[sell_order.asset].remove(sell_order)
                new_sell_order = Order(False, sell_order.quantity - buy_order.quantity, sell_order.asset,
                                       sell_order.price, sell_order.asset_money, sell_order.agent)
                sell_order.agent.orders[sell_order.asset].append(new_sell_order)
                assigned_sell_order = Order(False, buy_order.quantity, sell_order.asset, sell_order.price,
                                            sell_order.asset_money, sell_order.agent)
                self.sell_orders.insert(0, new_sell_order)
                pairings.append((buy_order, assigned_sell_order, (buy_order.price + assigned_sell_order.price) / 2))
            if len(self.buy_orders) == 0 or len(self.sell_orders) == 0:
                break
        return pairings


class Order:
    def __init__(self, buysell, quantity, asset, price, asset_money, agent):
        self.buysell = buysell
        self.asset_money = asset_money
        self.price = price
        self.asset = asset
        self.quantity = quantity
        self.agent = agent

    def __str__(self):
        if self.buysell:
            string = 'BUY'
        else:
            string = 'SELL'
        string += str(self.quantity) + self.asset.name + '@' + str(self.price) + self.asset_money.name + \
                  '--' + self.agent.name
        return string


class Agent:
    def __init__(self, name):
        self.name = name
        self.portfolio = dict()
        self.orders = dict()

    def __str__(self):
        return self.name

    def place_order(self, market, buysell, quantity, asset, price, asset_money):
        order = Order(buysell, quantity, asset, price, asset_money, self)
        if self.check_order(order):
            acknowledgment = market.acknowledge_place_order(order)
            if acknowledgment is True:
                if (market, asset) in self.orders:
                    self.orders.update({asset: self.orders[asset].append(order)})
                else:  # create new entry for (market, asset) in orders dictionary
                    self.orders.update({asset: [order]})

    def check_order(self, order):
        if order.buysell:  # BUY ORDER
            if order.asset_money in self.portfolio:
                pending_buyorders = 0
                if order.asset in self.orders:
                    for pend_order in self.orders[order.asset]:
                        if pend_order.buysell:
                            pending_buyorders += pend_order.price * pend_order.quantity
                if order.price * order.quantity > self.portfolio[order.asset_money] - pending_buyorders:
                    return False  # Not enough money
            else:
                return False
        else:  # SELL ORDER
            if order.asset in self.portfolio:
                pending_sellorders = 0
                if order.asset in self.orders:
                    for pend_order in self.orders[order.asset]:
                        if not pend_order.buysell:
                            pending_sellorders += pend_order.quantity
                if order.quantity > self.portfolio[order.asset] - pending_sellorders:
                    return False  # Not enough asset to sell
            else:
                return False
        return True

    def cancel_order(self, market, order):
        if order in self.orders:
            acknowledgment = market.acknowledge_cancel_order(order)
            if acknowledgment is True:
                self.orders[(market, order.asset)].remove(order)

    def print_state(self):
        print('Agent: ' + str(self.name))
        print('     Portfolio:')
        for asset, quantity in self.portfolio.items():
            print('         {0}: {1}'.format(asset.name, quantity))

    def print_orders(self):
        print('Agent: ' + str(self.name))
        print('     Orders:')
        for asset, order_list in self.orders.items():
            separator = '\n            '
            orders_str = separator
            for order in order_list:
                orders_str += order.__str__() + separator
            print('         {0}: {1}'.format(asset.name, orders_str))


if __name__ == '__main__':
    agent1 = Agent('A1')
    agent2 = Agent('A2')
    money = Money('USD', {agent1: 100, agent2: 200})
    eur = Money('EUR', {agent2: 200})
    shares = Asset('Shares', {agent1: 10, agent2: 0})

    nyse = Market('NYSE', [shares], [money])

    money.print_state()
    shares.print_state()
    agent1.place_order(nyse, False, 10, shares, 10, money)
    agent1.print_state()
    agent2.place_order(nyse, True, 10, shares, 10, money)
    print()
    agent1.print_orders()
    nyse.print_order_books()

    nyse.order_books[shares, money].match_orders()

    nyse.print_order_books()
