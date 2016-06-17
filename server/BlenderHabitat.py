import sys
import threading
import re
import time
import socket
from pymongo import MongoClient
from PyTango import DeviceProxy
from datetime import datetime as dt
import json

TCP_IP = '127.0.0.1'
TCP_PORT = 5040
BUFFER_SIZE = 10000


class Blender():

    def __init__(self):
        print "inside init"
        client = MongoClient('localhost', 27017)
        self.db = client.habitatdb
        self.threads = []
        self.nodeTimers = []
        self.isModified = False
        self.addingSummary = False
        self.summaryNode = None
        nodes = self.db.nodes
        self.checkedLeaves = []
        try:
            #print"yaha"
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind((TCP_IP, TCP_PORT))
            #print "idsd"
            self.sock.listen(1)
            #print"aaa"
            self.conn, self.addr = self.sock.accept()
            print 'Connection ESTAblished successfully to BlenderLeap Client'
            time.sleep(3)
            response="".encode()
            try:                   
                data = self.conn.recv(BUFFER_SIZE)
                print data
                if not data:
                    print "no data"
                if data=="add" or data=="Add":                	
	                try:
	                	data = self.conn.recv(BUFFER_SIZE)
	                   	response+=data
	                   	data_arr=json.loads(response)
	                   	self.devName=data_arr[0]
	                   	self.attrname=data_arr[1]
	                   	self.summary_type=data_arr[2]
	                   	self.summ_time=data_arr[3]
	                except:
	                    print "error in sending data"
                  	self.populate_startup_nodes()
                  	self.add_device()

                else:
                	try:
	                	data = self.conn.recv(BUFFER_SIZE)
		                response+=data
		                data_arr=json.loads(response)
		                #print data_arr
		                #print data
		                self.devName=data_arr[0]
		                self.attrname=data_arr[1]
	                	self.delete_node()
	                	self.populate_startup_nodes()
                	except:
                		print "delete error"
            except:
                print "Receiving error"
        except:
            print "connection couldn't be established to BlenderLeap Client"
            self.sock.close()
            sys.exit()
            pass
        #print self.devName,self.attrname,self.summary_type,self.summ_time
        
    def populate_startup_nodes(self):
        nodes = self.db.nodes
        print dt.now(), ":", 'populating leaves'
        for i in nodes.find({'type': 'leaf'}):
            device = i['name'] + " - " + i['attr']
            if device in self.checkedLeaves:
                continue
            proxy = DeviceProxy(i['name'])
            deviceFlag = 1
            while deviceFlag:
                try:
                    proxy.ping()
                    deviceFlag = 0
                    t = threading.Thread(target=self.aggregate_data,
                                         args=([device]))
                    t.start()
                    #self.update_tree(self.dataSourcesTreeItem, i['name'],
                                     #i['attr'])
                    self.checkedLeaves.append(device)
                except Exception as ex:
                    print "Warning"+ "Start the device server" + device
    
    def fetch_data(self, devName):
        temp = devName.split(" - ")
        dName = temp[0]
        dAttr = temp[1]
        proxy = DeviceProxy(dName)
        nodes = self.db.nodes
        node = nodes.find_one({'name': dName, 'attr': dAttr})
       	#print "inside fetch_data"
       	
       	#print proxy
       	#print dName
       	#print dAttr
        # print node
        # echo
        #conn.close()
        temp = proxy[dAttr].value
        if node != None:
            try:
                max_len = node['max_len']
                if len(list(node['data'])) >= max_len:
                    nodes.update(
                        {'name': dName, 'attr': dAttr}, {'$pop': {'data': -1}})
                nodes.update(
                    {'name': dName, 'attr': dAttr}, {'$push': {'data': temp}})
                node = nodes.find_one({'name': dName, 'attr': dAttr})
                summary_data = self.find_summary(
                    list(node['data']), node['function'])
                nodes.update(
                    {'name': dName, 'attr': dAttr}, {'$set': {'summary_data': summary_data}})
                response=dName+ " " + dAttr +" "+ node['function']+ "=" + " "+ str(node['summary_data']) 
                summary_value=str(node['summary_data'])
                try:
                    self.conn.send(response.encode()) 
                except:
                    print "could send please check connection"
                    self.sock.close()
                    sys.exit()
                    pass
                print response 
                threading.Timer(4, self.fetch_data, [devName]).start()
            except Exception as ex:
                print ex
                print node
        else:
            print devName, "deleted"
           
    def aggregate_data(self, devName):
        timer = threading.Timer(3, self.fetch_data, [devName])
        timer.start()
    
    def add_summary(self):
        summaryTime = ""
        max_len = 0
        #argv=sys.argv
        attrname=self.attrname
        summary_type=self.summary_type
        summ_time=self.summ_time
        children = ""
        attr = ""
        summary_children = {}
        nodes = self.db.nodes
        summary=summary_type
        pattern = re.compile("^[0-9][0-9]:[0-9][0-9]:[0-9][0-9]$")
        #print "here"
        #print summary
        #print summ_time
        #print attrname
        """
        if self.addingSummary == True:
            print "Adding summary"
            node = nodes.find_one({'name': self.summaryNode, 'attr': ""})
            summaryName = str(self.ui.summaryNameLE.text())
            if summaryName == "":
                QtGui.QErrorMessage(self).showMessage(
                    "Summary name cannot be empty. Please enter summary name")
                return
            children = []
            print summaryName
            model = self.ui.devicesListView.model()
            for i in range(model.rowCount()):
                item = model.item(i)
                itemText = str(item.text())
                if item.checkState() == QtCore.Qt.Checked:
                    children.append(itemText)
            if len(children) == 0:
                QtGui.QErrorMessage(self).showMessage(
                    "Select at least one child for summary!")
                return
            summary_children = node['summary_children']
            print summary_children
            summary_children[summaryName] = [children, summary]
            print summary_children
            nodes.update({'name': self.summaryNode, 'attr': ""},
                         {'$set': {'summary_children': summary_children}})
            self.addingSummary = False
            self.ui.groupBox.hide()
            self.ui.comboBox.hide()
            self.ui.attrLabel.hide()
            self.ui.devicesListView.hide()
            self.ui.summaryNameLE.hide()
            return
        """    
        sourceType = self.sourceType
        print "logging:", sourceType
        #self.ui.minButton.setChecked(True)
        if sourceType == "leaf":
            timeField = summ_time
            if len(timeField) == 0:
                print "Time Field is required"
                return
            if not pattern.match(timeField):
                print "Please enter time in the correct format -- hh:mm:ss"
                return
            l = timeField.split(":")
            attr = attrname
            summaryTime = int(l[0]) * 3600 + int(l[1]) * 60 + int(l[2])
            max_len = (summaryTime * 60) / 2
            nodeName = self.devName
            summary_data = 0.0
        node = {'name': nodeName,
                'type': sourceType,
                'attr': attr,
                'function': summary,
                'time': summaryTime,
                'children': children,
                'max_len': max_len,
                'data': [],
                'summary_data': summary_data,
                'summary_children': summary_children
                }

        #print node
        node_id = nodes.insert_one(node).inserted_id
        #print "inserted node:", nodes.find_one({'_id': node_id})
        if sourceType == "leaf":
            t = threading.Thread(
                target=self.aggregate_data, args=([self.devName + " - " + attr]))
            try:
                t.start()
            except (KeyboardInterrupt, SystemExit):
                    cleanup_stop_thread();
                    sys.exit()

    def delete_node(self):
    	"""
        message = "Are you sure you want to delete the node?"
        reply = QtGui.QMessageBox.question(self, 'Message', message,
                                           QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        """
        print "reached"
        if 1:
            nodes = self.db.nodes
            mdNode = self.devName
            mdAttr = self.attrname
            node=nodes.find_one({'name': mdNode, 'attr': mdAttr})
            if node:	
            	nodes.remove({'name': mdNode, 'attr': mdAttr})
            else:
            	print"Cannot delete. Invalid device name or attribute"
            """
            self.ui.treeWidget.clear()
            self.dataSourcesTreeItem = QtGui.QTreeWidgetItem(
                self.ui.treeWidget)
            self.dataSourcesTreeItem.setText(0, "Data Sources")
            self.build_tree()
            root = self.ui.treeWidget.invisibleRootItem()
            try:
                item = root.child(0)
                item = item.child(0)
            except Exception as ex:
                print ex
                item = root.child(0)
            self.ui.treeWidget.setCurrentItem(item)
            """

    def find_summary(self, data, function):
        if function == "Minimum":
            return min(data)
        elif function == "Maximum":
            return max(data)
        elif function == "Average":
            try:
                value = float(sum(data)) / len(data)
            except ZeroDivisionError:
                value = 0
            return value
            
    def add_device(self):
        print "Add new device"
        #argv=sys.argv
        devName = self.devName
        attrname=self.attrname
        self.devName = devName
        nodes = self.db.nodes
        #print devName
        if 1:
            try:
                self.sourceType = "leaf"
                self.proxy = DeviceProxy(devName)
                print "Device added success"
                dev_attrs = self.proxy.get_attribute_list()
                #print dev_attrs
                if nodes.find_one({'name': devName, 'attr':attrname}) != None:
                    print " attribute already added before sorry"
                else:
                    self.add_summary()
            except Exception as ex:
                print ex
                print "Incorrect Device Address"
        else:
            print "Warning"+"Device not added"


if __name__ == "__main__":
    #print"asd"
    myapp = Blender()
