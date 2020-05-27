import os
import django
os.environ['DJANGO_SETTINGS_MODULE'] = 'upsweb.settings'
django.setup()
from django.contrib.auth.models import User
from users.models import Profile
from orders.models import Order

# delete all the old data in the table
def clear_table(table_num):
    # table_num == 0 : Order
    # table_num == 1 : Profile
    if table_num == 0:
        Order.objects.all().delete()
    else:
        Profile.objects.all().delete()

# associate a amazon account with a UPS account, if success, return true; else return false
def associateAU(aAccountid, uAccountName, worldid):
    ups_users = Profile.objects.all()
    for u in ups_users:
        if u.user.username == uAccountName and u.worldid == worldid:
            u.aAccountid = aAccountid
            return u.user.id
    return -1

# add a order into orders table, if success, return true; else return false
def addOrder1(uAccountName, packageid, truck_id, x, y, worldid, products_num, productsids, products):
    try:
        if len(products_num) != len(productsids) and len(productsids) != len(products):
            return False
        ups_user = User.objects.get(username=uAccountName)
        if Order.objects.filter(package_id=packageid).exists():
            return False
        Order.objects.create(uAccount=ups_user, worldid=worldid, package_id=packageid, truck_id=truck_id,
                            destination_x=x, destination_y=y, products_num=products_num, 
                            products_id=productsids, products_description=products)
        return True
    except:
        return False
    return False

# add a order into orders table, if success, return true; else return false
def addOrder2(packageid, truck_id, x, y, worldid, products_num, productsids, products):
    try:
        if len(products_num) != len(productsids) and len(productsids) != len(products):
            return False
        if Order.objects.filter(package_id=packageid).exists():
            return False
        Order.objects.create(worldid=worldid, package_id=packageid, truck_id=truck_id, destination_x=x, destination_y=y, 
                            products_num=products_num, products_id=productsids, products_description=products)
        return True
    except:
        return False


# check whether a UPS account exists, if so return true, otherwise return false
def find_uAccount(uAccountName):
    try:
        print(uAccountName)
        ups_user = User.objects.get(username=uAccountName)
        return ups_user.id
    except:
        return -1


# change the packages' status in the truck and return all the packages' id and location(x & y)
def change_status(truck_id, status_num):
    ids = []
    xs = []
    ys = []
    status = 'status1'
    if status_num == 2:
        status = 'status2'
    elif status_num == 3:
        status = 'status3'
    elif status_num == 4:
        status = 'status4'
    try:
        orders = Order.objects.filter(truck_id=truck_id)
        for o in orders:
            if o.status == 'status4':
                continue
            o.status = status
            o.save()
            ids.append(o.package_id)
            xs.append(o.destination_x)
            ys.append(o.destination_y)
        return ids, xs, ys
    except:
        print("Error happened when changing the status of packages\n")
        return ids, xs, ys


# change a package's status
def change_package_status(packageid, status_num):
    status = 'status1'
    if status_num == 2:
        status = 'status2'
    elif status_num == 3:
        status = 'status3'
    elif status_num == 4:
        status = 'status4'
    
    try:
        order = Order.objects.get(package_id=packageid)
        order.status = status
        order.save()
        return True
    except:
        return False


