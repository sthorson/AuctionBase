#!/usr/bin/env python

import sys; sys.path.insert(0, 'lib') # this line is necessary for the rest
import os                             # of the imports to work!

import web
import sqlitedb
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

###########################################################################################
##########################DO NOT CHANGE ANYTHING ABOVE THIS LINE!##########################
###########################################################################################

######################BEGIN HELPER METHODS######################

# helper method to convert times from database (which will return a string)
# into datetime objects. This will allow you to compare times correctly (using
# ==, !=, <, >, etc.) instead of lexicographically as strings.

# Sample use:
# current_time = string_to_time(sqlitedb.getTime())

def string_to_time(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

# helper method to render a template in the templates/ directory
#
# `template_name': name of template file to render
#
# `**context': a dictionary of variable names mapped to values
# that is passed to Jinja2's templating engine
#
# See curr_time's `GET' method for sample usage
#
# WARNING: DO NOT CHANGE THIS METHOD
def render_template(template_name, **context):
    extensions = context.pop('extensions', [])
    globals = context.pop('globals', {})

    jinja_env = Environment(autoescape=True,
            loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
            extensions=extensions,
            )
    jinja_env.globals.update(globals)

    web.header('Content-Type','text/html; charset=utf-8', unique=True)

    return jinja_env.get_template(template_name).render(context)

#####################END HELPER METHODS#####################

        # TODO: add additional URLs here
        # first parameter => URL, second parameter => class name

urls = ('/', 'index',
	'/currtime', 'curr_time',
        '/selecttime', 'select_time',
	'/search', 'search',
	)

class index:
	def GET(self):
		return render_template('app_base.html')

class curr_time:
    # A simple GET request, to '/currtime'
    #
    # Notice that we pass in `current_time' to our `render_template' call
    # in order to have its value displayed on the web page
    def GET(self):
        current_time = sqlitedb.getTime()
        return render_template('curr_time.html', time = current_time)

class select_time:
    # Aanother GET request, this time to the URL '/selecttime'
    def GET(self):
        return render_template('select_time.html')

    # A POST request
    #
    # You can fetch the parameters passed to the URL
    # by calling `web.input()' for **both** POST requests
    # and GET requests
    def POST(self):
        post_params = web.input()
        MM = post_params['MM']
        dd = post_params['dd']
        yyyy = post_params['yyyy']
        HH = post_params['HH']
        mm = post_params['mm']
        ss = post_params['ss'];
        enter_name = post_params['entername']


        selected_time = '%s-%s-%s %s:%s:%s' % (yyyy, MM, dd, HH, mm, ss)
        update_message = 'Welcome to the future, %s! Time has progressed to: %s.' % (enter_name, selected_time)
	err_message = "A problem occurred, the time was not updated. Remember, time can only go forwards!"
        #save the selected time as the current time in the database
	if (sqlitedb.setTime(selected_time)):
        	# Here, we assign `update_message' to `message', which means
        	# we'll refer to it in our template as `message'
        	return render_template('select_time.html', message = update_message)
	else:
		return render_template('select_time.html', message = err_message)

class search: #TODO: IMPLEMENT SEARCH FUNCTION AND ALL QUERIES


	def GET(self):
		return render_template('search.html')

	def POST(self):
		#Get parameters from form
		params = web.input() #If form not filled, defaults entry to null
		item_id = params['itemID']
		user_id = params['userID']
		min_price = params['minPrice']
		max_price = params['maxPrice']
		status = params['status']

		#LOGIC BLOCK - to determine what query to run
		#start w/ base query and add up
		if (status == 'open'):

			query_string = "select * from Items i, CurrentTime ct where ct.Time < i.Ends"

			if (item_id):
				query_string += " AND i.ItemID = '%(itemID)s' "%{'itemID':item_id}
			if (user_id):
				query_string += " AND s.UserID = '%(userID)s' "%{'userID':user_id}
			if (min_price):
				query_string += " AND i.Currently >= '%(minPrice)s' "%{'minPrice':min_price}
			if (max_price):
				query_string += " AND i.Currently <= '%(maxPrice)s' AND i.Buy_Price <= '%(maxPrice)s' "%{'maxPrice':max_price}
			
		elif (status == 'close'):

			query_string = "select * from Items i, CurrentTime ct where ct.Time >= i.Ends"

			if (item_id):
				query_string += " AND i.ItemID = '%(itemID)s' "%{'itemID':item_id}
			if (user_id):
				query_string += " AND i.Seller_UserID = '%(userID)s' "%{'userID':user_id}
			if (min_price):
				query_string += " AND i.Currently >= '%(minPrice)s' "%{'minPrice':min_price}
			if (max_price):
				query_string += " AND i.Currently <= '%(maxPrice)s' AND i.Buy_Price <= '%(maxPrice)s' "%{'maxPrice':max_price}
		
		elif (status == 'notStarted'):

			query_string = "select * from Items i, CurrentTime ct where ct.Time < i.Started"

			if (item_id):
				query_string += " AND i.ItemID = '%(itemID)s' "%{'itemID':item_id}
			if (user_id):
				query_string += " AND i.Seller_UserID = '%(userID)s' "%{'userID':user_id}
			if (min_price):
				query_string += " AND i.Currently >= '%(minPrice)s' "%{'minPrice':min_price}
			if (max_price):
				query_string += " AND i.Currently <= '%(maxPrice)s' AND i.Buy_Price <= '%(maxPrice)s' "%{'maxPrice':max_price}

		else: #status == all

			query_string = "select * from Items i"

			if ((not item_id) or (not user_id) or (not min_price) or (not max_price)):
				query_string += " where i.Buy_Price > 0"

			if (item_id):
				query_string += " AND i.ItemID = '%(itemID)s' "%{'itemID':item_id}
			if (user_id):
				query_string += " AND i.Seller_UserID = '%(userID)s' "%{'userID':user_id}
			if (min_price):
				query_string += " AND i.Currently >= '%(minPrice)s' "%{'minPrice':min_price}
			if (max_price):
				query_string += " AND i.Currently <= '%(maxPrice)s' AND i.Buy_Price <= '%(maxPrice)s' "%{'maxPrice':max_price}

		#END OF LOGIC BLOCK
		print str(query_string) #for debug
		#Run the query
		t = sqlitedb.transaction()
		try:
			results = sqlitedb.query(query_string)
		except Exception as e:
			t.rollback()
			print str(e)
			return render_template('search.html', message = "A problem occurred.", key = results)	
		else:
			t.commit()
			return render_template('search.html', key = results)

			

# Templates / notes
# return render_template('select_time.html', message = update_message)
# where="Time = '%(oldTime)s'"%{"oldTime":old_time}
# t = sqlitedb.transaction()
# try:
#     sqlitedb.query('[FIRST QUERY STATEMENT]')
#     sqlitedb.query('[SECOND QUERY STATEMENT]')
# except Exception as e:
#     t.rollback()
#     print str(e)
# else:
#     t.commit()

#query_string = 'select * from Items where item_ID = $itemID'
#result = query(query_string, {'itemID': item_id})

###########################################################################################
##########################DO NOT CHANGE ANYTHING BELOW THIS LINE!##########################
###########################################################################################

if __name__ == '__main__':
    web.internalerror = web.debugerror
    app = web.application(urls, globals())
    app.add_processor(web.loadhook(sqlitedb.enforceForeignKey))
    app.run()
