#!/usr/bin/env python

"""

To run locally:

    python server.py

Go to http://localhost:8111 in your browser.

"""

import os, time
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = os.urandom(24)


#
# You will need to modify the URI to connect to your database in order to use the data.
#

DATABASEURI = ""


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print ("connecting to database failed")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


@app.route('/', methods=["GET"])
def index():

  # DEBUG: this is debugging code to see what request looks like
  print (request.args)
  return render_template("index.html")


@app.route('/login', methods=["GET"])
def login():
  print (request.args)
  if "loggedin" in session and session["loggedin"]:
    return redirect('/')
  return render_template("login.html")

@app.route('/login', methods=["POST"])
def loginVerify():
    username = request.form['username']
    password = request.form['password']
    tp = request.form['account_type']
    if tp == "customer":
        cursor = g.conn.execute("select uid, uname from customers where uid= %(uid)s AND pwd=%(pwd)s", {'uid':username, 'pwd':password})
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = username
            session['username'] = account["uname"]
            session['type'] = tp
            return redirect('/')
        else:
            msg = 'Incorrect username or password'
            return render_template('login.html', msg=msg)
    else:
        cursor = g.conn.execute("select sid, sname from retailers where sid=%(uid)s AND pwd=%(pwd)s", {'uid':username, 'pwd':password})
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = username
            session['username'] = account["sname"]
            session['type'] = tp
            return redirect('/')
        else:
            msg = 'Incorrect username or password'
            return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
  print(request.args)
  if "loggedin" in session:
    session['loggedin'] = False
  return redirect('/')

@app.route('/p', methods=["GET"])
def products():
  print (request.args)
  cursor = g.conn.execute("SELECT G.gname, R.sname, C.cname, G.gid, S.sid, S.price FROM goods_in G, sells S, retailers R, categories C where G.gid = S.gid AND S.sid = R.sid AND C.cid = G.cid")
  gnames = []
  snames = []
  category = []
  gid = []
  sid = []
  price = []
  for result in cursor:
    gnames.append(result[0])
    snames.append(result[1])
    category.append(result[2])
    gid.append(result[3])
    sid.append(result[4])
    price.append(result[5])
  cursor.close()
  context = dict(gnames = gnames, snames = snames, category = category, price = price, gid = gid, sid = sid)
  return render_template("products.html", **context)

@app.route('/u')
def user():
  print(request.args)
  if 'loggedin' not in session or not session['loggedin']:
    return redirect('/')
  if session["type"] == "customer":
    cursor = g.conn.execute("select O.oid, O.date, O.cost from orders_pg O where O.uid = '%s'" %(session["id"]))
    dates = []
    costs = []
    oids = []
    for result in cursor:
      oids.append(result[0])
      dates.append(result[1])
      costs.append(result[2])
    cursor = g.conn.execute("select A.addr from delivers_to D, addresses A where D.uid = '%s' AND A.addr_id = D.addr_id" %(session["id"]))
    addr = []
    for result in cursor:
      addr.append(result[0])
    cursor = g.conn.execute("select T.tel_num from c_tel C, telephone_numbers T where C.uid = '%s' AND T.tel_id = C.tel_id" %(session["id"]))
    tel = []
    for result in cursor:
      tel.append(result[0])
    context = dict(oids = oids, dates = dates, costs = costs, addr = addr, tel = tel)
    return render_template("customer.html", **context)
  else:
    cursor = g.conn.execute("select G.gname, S.price from sells S, Goods_in G where S.sid = '%s' AND G.gid = S.gid" %(session["id"]))
    goods = []
    price = []
    for result in cursor:
      goods.append(result[0])
      price.append(result[1])
    cursor = g.conn.execute("select A.addr from delivers_from D, addresses A where D.sid = '%s' AND A.addr_id = D.addr_id" %(session["id"]))
    addr = []
    for result in cursor:
      addr.append(result[0])
    cursor = g.conn.execute("select T.tel_num from s_tel C, telephone_numbers T where C.sid = '%s' AND T.tel_id = C.tel_id" %(session["id"]))
    tel = []
    for result in cursor:
      tel.append(result[0])
    cursor = g.conn.execute("select G.gname, R.oid, R.date, R.qty, R.cost, C.uname from rg R, orders_pg O, customers C, goods_in G where R.sid='%s' AND G.gid=R.gid AND O.oid=R.oid AND C.uid=O.uid" %(session["id"]))
    ogname = []
    oid = []
    odate = []
    oqty = []
    ocost = []
    ocname = []
    for result in cursor:
      ogname.append(result[0])
      oid.append(result[1])
      odate.append(result[2])
      oqty.append(result[3])
      ocost.append(result[4])
      ocname.append(result[5])
    context = dict(goods = goods, price = price, addr = addr, tel = tel, ogname = ogname, oid = oid, odate = odate, oqty = oqty, ocost = ocost, ocname = ocname)
    return render_template("retailer.html", **context)

@app.route('/register', methods=["GET"])
def register():
  print(request.args)
  return render_template("register.html")

@app.route('/register', methods=["POST"])
def registerVerify():
  print(request.args)
  tp = request.form['account_type']
  uid = request.form['username']
  name = request.form['fullname']
  pw = request.form['password']
  if tp == 'customer':
    cursor = g.conn.execute("select uid from customers where uid = %(uid)s", {'uid':uid})
    res = cursor.fetchone()
    if res:
      msg = "username already exists"
      return render_template("register.html", msg=msg)
    g.conn.execute("INSERT INTO customers VALUES (%(uid)s, %(name)s, %(pw)s)", {'uid':uid, 'name':name, 'pw':pw})
  else:
    cursor = g.conn.execute("select sid from retailers where sid = %(uid)s", {'uid':uid})
    res = cursor.fetchone()
    if res:
      msg = "username already exists"
      return render_template("register.html", msg=msg)
    g.conn.execute("INSERT INTO retailers VALUES (%(uid)s, %(name)s, %(pw)s)", {'uid':uid, 'name':name, 'pw':pw})
  return redirect('/')

@app.route('/o/<oid>')
def order(oid):
  print(request.args)
  cursor = g.conn.execute("select O.date, O.cost as tcost, O.uid, S.sname, G.gname, R.qty, R.cost from orders_pg O, rg R, goods_in G, retailers S where O.oid = %(oid)s AND R.oid = O.oid AND G.gid = R.gid AND S.sid = R.sid", {'oid':oid})
  res = cursor.fetchone()
  date = res['date']
  tcost = res['tcost']
  uid = res['uid']
  sname = [res['sname']]
  gname = [res['gname']]
  qty = [res['qty']]
  cost = [res['cost']]
  if 'loggedin' not in session or not session['loggedin'] or session['type']!="customer" or session['id'] != uid :
    return "Access Denied"
  
  for result in cursor:
    sname.append(result['sname'])
    gname.append(result['gname'])
    qty.append(result['qty'])
    cost.append(result['cost'])
  context = dict(oid = oid, date = date, tcost = tcost, sname = sname, gname = gname, qty = qty, cost = cost)
  return render_template('order.html', **context)

@app.route('/addcart', methods=["POST"])
def addcart():
  print(request.args)
  gid = request.form["gid"]
  sid = request.form["sid"]
  qty = eval(request.form["qty"])
  if "cartItem" not in session:
    session["cartItem"] = []
    session["cartQty"] = []
  cartItem = session["cartItem"]
  cartQty = session["cartQty"]
  if (gid, sid) in cartItem:
    cartQty[cartItem.index((gid, sid))] += qty
  else:
    cartItem.append((gid, sid))
    cartQty.append(qty)
  session["cartItem"] = cartItem
  session["cartQty"] = cartQty
  return redirect("/p")

@app.route('/c')
def cart():
  print(request.args)
  if "cartItem" in session:
    cartItem = session["cartItem"]
    cartQty = session["cartQty"]
  else:
    cartItem = []
    cartQty = []
  gname = []
  sname = []
  price = []
  tprice = []
  gid = []
  sid = []
  sumCost = 0
  for gi, si in cartItem:
    cursor = g.conn.execute("select G.gname, R.sname, S.price from goods_in G, retailers R, sells S where G.gid='%s' AND R.sid='%s' AND G.gid=S.gid AND R.sid=S.sid" %(gi, si))
    res = cursor.fetchone()
    gname.append(res[0])
    sname.append(res[1])
    price.append(res[2])
    gid.append(gi)
    sid.append(si)
  for i in range(len(price)):
    tprice.append(price[i] * cartQty[i])
    sumCost += price[i] * cartQty[i]
  dcid = []
  dcrate = []
  finalCost = sumCost
  if "loggedin" in session and session["loggedin"] and session["type"]=="customer":
    cursor = g.conn.execute("select E.dcid, D.rate from eligible E, discounts D where E.uid='%s' AND D.dcid = E.dcid" %(session["id"]))
    for row in cursor:
      dcid.append(row[0])
      dcrate.append(row[1])
  if "discount" in session:
    rate = g.conn.execute("select rate from discounts where dcid='%s'" %(session["discount"])).fetchone()[0]
    finalCost = sumCost * (1 - rate / 100)
  context = dict(gname = gname, sname = sname, price = price, tprice = tprice, qty = cartQty, gid = gid, sid = sid, sumCost = sumCost, finalCost = finalCost, dcid=dcid, dcrate = dcrate)
  return render_template('cart.html', **context)

@app.route('/updatecart', methods=["POST"])
def updateCart():
  print(request.args)
  gid = request.form["gid"]
  sid = request.form["sid"]
  qty = eval(request.form["qty"])
  cartItem = session["cartItem"]
  cartQty = session["cartQty"]
  if qty == 0:
    cartQty.pop(cartItem.index((gid, sid)))
    cartItem.remove((gid, sid))
  else:
    cartQty[cartItem.index((gid, sid))] = qty
  session["cartItem"] = cartItem
  session["cartQty"] = cartQty
  return redirect('/c')

@app.route('/mkorder', methods=["POST"])
def mkorder():
  print(request.args)
  if 'loggedin' not in session or session["type"] != "customer":
    return render_template("login.html", msg="You must login as a customer to continue")
  cartItem = session["cartItem"]
  cartQty = session["cartQty"]
  gname = []
  sname = []
  price = []
  tprice = []
  gid = []
  sid = []
  sumCost = 0
  date = time.strftime("%Y-%m-%d")
  oid = session["id"][-5:] + str(int(time.time()))
  uid = session["id"]
  if 'discount' in session:
    dcid = session["discount"]
  for gi, si in cartItem:
    cursor = g.conn.execute("select G.gname, R.sname, S.price from goods_in G, retailers R, sells S where G.gid='%s' AND R.sid='%s' AND G.gid=S.gid AND R.sid=S.sid" %(gi, si))
    res = cursor.fetchone()
    gname.append(res[0])
    sname.append(res[1])
    price.append(res[2])
    gid.append(gi)
    sid.append(si)
  for i in range(len(gid)):
    tprice.append(price[i] * cartQty[i])
    sumCost += price[i] * cartQty[i]
  if "discount" in session:
    rate = g.conn.execute("select rate from discounts where dcid='%s'" %(session["discount"])).fetchone()[0]
    sumCost = sumCost * (1 - rate / 100)
  
  g.conn.execute("insert into orders_pg values('%s', '%s', %s, '%s')" %(oid, uid, sumCost, date))
  for i in range(len(gid)):
    g.conn.execute("insert into rg values('%s', %s, %s, '%s', '%s', '%s')" %(oid, cartQty[i], tprice[i], date, sid[i], gid[i]))
  session["cartItem"] = []
  session["cartQty"] = []
  if 'discount' in session:
    session.pop("discount")
    g.conn.execute("delete from eligible where dcid='%s' AND uid='%s'" %(dcid, uid))
    g.conn.execute("insert into apply values('%s', '%s')" %(oid, dcid))
  return redirect('/o/%s' %(oid))

@app.route('/addr', methods=["GET"])
def addAddr():
  print(request.args)
  return render_template("addr.html")

@app.route('/addr', methods=["POST"])
def confirmAddr():
  print(request.args)
  addr = request.form["addr"]
  addr_id = session["id"][-5:] + str(int(time.time()))
  g.conn.execute("insert into addresses values(%(addrid)s, %(addr)s)", {'addrid':addr_id, 'addr':addr})
  if session["type"] == "customer":
    g.conn.execute("insert into delivers_to values(%(uid)s, %(id)s)", {'uid':session["id"], 'id':addr_id})
  else:
    g.conn.execute("insert into delivers_from values(%(uid)s, %(id)s)", {'uid':session["id"], 'id':addr_id})
  return redirect('/u')

@app.route('/tel', methods=["GET"])
def addTel():
  print(request.args)
  return render_template("tel.html")

@app.route('/tel', methods=["POST"])
def confirmTel():
  print(request.args)
  tel = request.form["tel"]
  tel_id = session["id"][-5:] + str(int(time.time()))
  g.conn.execute("insert into telephone_numbers values(%(telid)s, %(tel)s)", {'telid':tel_id, 'tel':tel})
  if session["type"] == "customer":
    g.conn.execute("insert into c_tel values(%(uid)s, %(id)s)", {'uid':session["id"], 'id':tel_id})
  else:
    g.conn.execute("insert into s_tel values(%(uid)s, %(id)s)", {'uid':session["id"], 'id':tel_id})
  return redirect('/u')

@app.route('/chooseproduct', methods=["GET"])
def chooseProduct():
  print(request.args)
  if 'loggedin' not in session or not session['loggedin'] or session['type']!="retailer":
    return redirect('/')
  cursor = g.conn.execute("select G.gid, G.gname, C.cname from goods_in G, categories C where G.cid = C.cid AND G.gid not in (select gid from sells where sid = '%s')" %(session['id']))
  gid = []
  gname = []
  category = []
  for rows in cursor:
    gid.append(rows[0])
    gname.append(rows[1])
    category.append(rows[2])
  context = dict(gid = gid, gname = gname, category = category)
  return render_template('chooseproduct.html', **context)

@app.route('/chooseproduct', methods=["POST"])
def choosepConfirm():
  print(request.args)
  gid = request.form["gid"]
  price = eval(request.form["price"])
  sid = session["id"]
  g.conn.execute("insert into sells values('%s', '%s', %s)" %(sid, gid, price))
  return redirect('/u')

@app.route('/addproduct', methods=["GET"])
def addProduct():
  print(request.args)
  if 'loggedin' not in session or not session['loggedin'] or session['type']!="retailer":
    return redirect('/')
  cursor = g.conn.execute("select C.cname, C.cid from categories C")
  cname = []
  cid = []
  for rows in cursor:
    cname.append(rows[0])
    cid.append(rows[1])
  context = dict(cname = cname, cid = cid)
  return render_template('addproduct.html', **context)

@app.route('/addproduct', methods=["POST"])
def addpConfirm():
  print(request.args)
  gname = request.form["gname"]
  gid = gname[-5:] + str(int(time.time()))
  cid = request.form["cid"]
  g.conn.execute("insert into goods_in values(%(gid)s, %(gn)s, %(cid)s)", {'gid':gid, 'gn':gname, 'cid':cid})
  return redirect('/chooseproduct')

@app.route('/getdc')
def getdc():
  if 'loggedin' not in session or not session['loggedin'] or session['type']!="customer":
    return redirect('/')
  uid = session['id']
  cursor = g.conn.execute("select uid from eligible where dcid='1' AND uid='%s'" %(uid))
  res = cursor.fetchone()
  if res:
    return redirect('/')
  g.conn.execute("insert into eligible values('%s', '1')" %(uid))
  return redirect('/')

@app.route('/applydc', methods=["POST"])
def applydc():
  if 'loggedin' not in session or not session['loggedin'] or session['type']!="customer":
    return redirect('/c')
  dcid = request.form["dcid"]
  session['discount'] = dcid
  return redirect('/c')

@app.route('/canceldc')
def canceldc():
  if 'loggedin' not in session or not session['loggedin'] or session['type']!="customer" or 'discount' not in session:
    return redirect('/c')
  session.pop('discount')
  return redirect('/c')


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print ("running on %s:%d" %(HOST, PORT)) 
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
