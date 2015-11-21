#!C:\Python27\python.exe
import cgi, cgitb, glob, time, os, sqlite3, Cookie, re, datetime, smtplib
from email.mime.text import MIMEText

def send_email(email, message, subject):
    #send a confirmation email to the new user
    #print 'Content-Type: text/plain\n\n'
    to_address = email
    from_address = 'andrewt@cse.unsw.edu.au'

    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = from_address
    msg['To'] = to_address
    s = smtplib.SMTP('smtp.unsw.edu.au')
    s.sendmail(from_address, [to_address], msg.as_string())
    s.quit()
    #send a confirmation email to the new user

def main():
    global cookie
    global flag_create_account_successfully
    global flag_activate_account
    global flag_logout
    global flag_post_successfully
    cgitb.enable()
    parameters = cgi.FieldStorage()      	#FieldStorage(None, None, [])  now

    self_username = ""
    string_cookie = os.environ.get('HTTP_COOKIE')
    if string_cookie:
        cookie.load(string_cookie)
        if 'sid' in cookie:
            self_username = cookie['sid'].value

    flag_create_account_successfully = 0
    if parameters.getvalue('register'):
        result = register(parameters)         #check whether the page should be redirected to register.html according to the legality of the input value
        if result.isdigit(): # "1"
            flag_activate_account = int(result)
            #flag_create_account_successfully = int(result)
        else:
            print result   #redirect happens here

    # logout handle
    if parameters.getvalue('action') == 'logout' and not parameters.getvalue('login'):
        flag_logout = 1
        #delete related session here
        cookie['sid'] = ''
        cookie['sid']['expires'] = 'Thu, 01 Jan 1970 00:00:00 GMT'
        print cookie
        #print "Set-Cookie: sid=\'\'"
        #delete related session here
        prompt_logout = "logout successfully."
    else:
        prompt_logout = ""
    # logout handle

    # activate account handle
    activate(parameters)
    recover_password(parameters)

    # self post bleat handle
    #BLEAT: id, username content time longitude latitude in_reply_to
    if parameters.getvalue('content'):
        flag_post_successfully = 1
        string_cookie = os.environ.get('HTTP_COOKIE')
        cookie.load(string_cookie)
        content = parameters.getvalue('content')

        conn = sqlite3.connect('users.db')
        #their username is mentioned in a bleat
        p = re.compile(r'@([\S]+)')
        at_result = p.findall(content)
        for at_value in at_result:
            cursor = conn.execute("SELECT username, email from user where username=?", (at_value,))
            for row in cursor: # only one record
                username = row[0]
                if username:
                    email = row[1]
                    message = """
                        Hi, the user %s mentioned you in bleat just now :)
                    """ % self_username
                    subject = "Bleat mention from Bitter"
                    send_email(email, message, subject)
            cursor.close()
        #their username is mentioned in a bleat

        time_current = time.time()
        longitude = parameters.getvalue('longitude')
        latitude = parameters.getvalue('latitude')
        # insert

        cursor = conn.execute("SELECT max(id) from bleat")
        id_largest = 0
        for row in cursor:
            id_largest = row[0]
        id = id_largest + 1

        conn.execute("INSERT INTO BLEAT (ID, USERNAME, CONTENT, TIME, LONGITUDE, LATITUDE) \
                 VALUES (?, ?, ?, ?, ?, ?);", (id, self_username, content, time_current, longitude, latitude))
        conn.commit()
        conn.close()

    page = parameters.getvalue("page", 0)
    if page < 0:
        page = 0
    # self post bleat handle
    prompt_login = checkLogin(parameters) #prompt_login is the message to show whether the user has login in
    print page_header()  #header actually should be processd, it contain home, about, register, and username sign in with password
    print user_page(prompt_login, prompt_logout, parameters)
    #print self_bleat()
    print bleats_page(page)
    print page_trailer(parameters)

def recover_password(parameters):
    global flag_recover_password
    if parameters.getvalue('recover_password'):
        username, password = '', ''
        user_email = parameters.getvalue('email')

        conn = sqlite3.connect('users.db')
        cursor = conn.execute("SELECT username, password from user where email=?;", (user_email, ))
        for row in cursor: # only one record
            username = row[0]
            password = row[1]
            if not username or not password:
                flag_recover_password_successfully = 0
        conn.close()
        #send a confirmation email to the new user
        message = """
            Hi, %s! your current password is: %s
            http://localhost/cgi-bin/bitter.cgi
        """ % (username, password)
        subject = 'Email Recovery from Bitter'

        send_email(user_email, message, subject)
        flag_recover_password = 1
        #send a confirmation email to the new user
    return

def activate(parameters):
    global flag_create_account_successfully
    global flag_activate_exception
    flag_contain = False
    index_delete = -1
    if parameters.getvalue('activate'):
        username = parameters.getvalue('username')
        f = open('tmp_user_account', 'r')
        f.seek(0)
        result_list = f.readlines()
        for i in range(len(result_list)):
            user_pass_email_list = result_list[i].split()
            if user_pass_email_list and user_pass_email_list[0] == username:
                newUsername = user_pass_email_list[0]
                newPassword = user_pass_email_list[1]
                newEmail = user_pass_email_list[2]
                conn = sqlite3.connect('users.db')

                cursor1 = conn.execute("SELECT username from user")
                cursor2 = conn.execute("SELECT password from user")
                cursor3 = conn.execute("SELECT email from user")
                for row in cursor1:
                    if newUsername in row[0]:
                        flag_activate_exception = 1
                        return

                for row in cursor2:
                     if newPassword in row[0]:
                        flag_activate_exception = 1
                        return

                for row in cursor3:
                    if newEmail in row[0]:
                        flag_activate_exception = 1
                        return

                index_delete = i
                conn.execute("INSERT INTO USER (USERNAME,PASSWORD,EMAIL) \
                             VALUES (?, ?, ?);", (newUsername, newPassword, newEmail))
                conn.commit()
                conn.close()

                flag_create_account_successfully = 1
                flag_contain = True
                break
        f.seek(0)
        f.close()
        if flag_contain == False:
            flag_activate_exception = 1
        else:
            del result_list[index_delete]
            tmp_file = "\n".join(result_list)
            tmp_file += "\n"
            fw = open('tmp_user_account', 'w')
            fw.write(tmp_file)
            fw.seek(0)
            fw.close()
    return


def register(parameters):
    newUsername = parameters.getvalue('username')
    newPassword = parameters.getvalue('password')
    newEmail = str(parameters.getvalue('email'))

    conn = sqlite3.connect('users.db')
    #id username password full_name email home_suburb home_latitude home_longitude profile
    cursor1 = conn.execute("SELECT username from user")
    cursor2 = conn.execute("SELECT password from user")
    cursor3 = conn.execute("SELECT email from user")

    for row in cursor1:
        if newUsername in row[0]:
            return redirect("views/register.html")
            #print "This username is used before, please use other one!"

    for row in cursor2:
         if newPassword in row[0]:
            return redirect("views/register.html")
            #print "This username is used before, please use other one!"

    for row in cursor3:
        if newEmail in row[0]:
            return redirect("views/register.html")
            #print "This username is used before, please use other one!"

    fw = open('tmp_user_account', 'a')
    fw.write(newUsername + " " + newPassword + " " + newEmail + "\n")
    fw.seek(0)
    fw.close()
    #send a confirmation email to the new user
    message = """
        Hi, I am bitter. Thanks for registration! Please click the below link to activate your account\n
        http://localhost/cgi-bin/bitter.cgi?activate=true&username=%s
    """ % newUsername
    subject = 'Email Confirmation from Bitter'

    send_email(newEmail, message, subject)
    #send a confirmation email to the new user

    global flag_activate_account
    flag_activate_account = 1
    return "%d" % flag_activate_account

def checkLogin(parameters):
    global cookie
    prompt_login = ""
    global flag_login_successfully
    if parameters.getvalue('login'):  #has login in
        username = parameters.getvalue('username')
        password = parameters.getvalue('password')

        conn = sqlite3.connect('users.db')
        #id username password full_name email home_suburb home_latitude home_longitude profile
        cursor1 = conn.execute("SELECT username from user")
        for row in cursor1:
            if username == row[0]:  # harry
                cursor2 = conn.execute("SELECT password from USER WHERE username=?", (username,))  #can only provide one zhanweifu with ( ,)
                for row in cursor2:
                    if password == row[0]:
                        flag_login_successfully = 1
                        prompt_login = "login successfully!"
                        # session should be processed here !

                        #cookie = Cookie.SimpleCookie()

                        cookie['sid'] = username  #set username in the cookie
                        cookie['sid']['expires'] = 12 * 30 * 24 * 60 * 60
                        print cookie
                        # session should be processed here !
                        conn.close()
                        return prompt_login
                    else:
                        prompt_login = "the password is incorrect!"
                        conn.close()
                        return prompt_login

        prompt_login = "the username doesn't exist!"
        conn.close()
        return prompt_login
    return prompt_login


def bleats_page(page):
    global cookie
    global flag_login_successfully
    username = ""
    string_cookie = os.environ.get('HTTP_COOKIE')
    if string_cookie:
        cookie.load(string_cookie)
        if 'sid' in cookie:
            username = cookie['sid'].value

    conn = sqlite3.connect('users.db')
    cursor = conn.execute("SELECT count(*) from bleat where (username in (select friend from listen where username=?) or username = ?) and in_reply_to is null order by time DESC",(username, username))
    rows = cursor.fetchone()[0]
    number_of_page = rows // 12
    if rows % 12 == 0 and rows != 0:
        number_of_page -= 1
    ##### control the beginning number of pages #####
    offset = int(page) * 12
    limit = 12

    if (username != "" or flag_login_successfully == 1) and flag_logout == 0: #has already login
        cursor = conn.execute("SELECT username, content, time, id from bleat where (username in (select friend from listen where username=?) or username = ?) and in_reply_to is null order by time DESC limit ? offset ?;",(username, username, limit, offset))
    else:
        #username content time longitude latitude in_reply_to
        cursor = conn.execute("SELECT username, content, time, id from bleat where in_reply_to is null order by time DESC limit ? offset ?;",(limit, offset))
    html = "<hr>"
    if cursor:
        html += "<div class=\"container\">"
    block = 0
    date_time = ""
    for row in cursor:
        if block % 2 == 0:
            html += "<div class=\"row\">"
        other_username = row[0]

        avatar = ""
        cursor1 = conn.execute("SELECT profile from user where username=?;", (other_username ,))
        for row1 in cursor1:
            avatar = row1[0]
        if avatar:
            url_avatar = "<img src=\"%s\" alt=\"Bitter\" class=\"img-circle\" height=\"50px\" width=\"50px\">" % avatar
        else:
            url_avatar = "<img src=\"avatar/default.jpg\" alt=\"Bitter\" class=\"img-circle\" height=\"50px\" width=\"50px\">"

        content = row[1]
        timestamp = row[2]
        id = row[3] #for view details
        date_time = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

        user_link = ""
        bleat_detail_link = ""
        if (username != "" or flag_login_successfully == 1) and flag_logout == 0:
            # create internal link for both other users and me who are being @, for other users, create a link, for myself, just bold it
            content = row[1]
            p1 = re.compile(r'@([\S]+)')
            at_result = p1.findall(content)  # list : ['DaisyFuentes', 'DaisyFuentes']   at_result is a list contains only one bleat
            for at_value in at_result:
                if at_value == username:   # the value behind @ is a myself
                    # create internal link for @user
                    oldstr = '@' + at_value
                    newstr = "@<b> %s </b>" % at_value
                    content = content.replace(oldstr, newstr, 1)
                    # create internal link for @user
                else:
                    cursor2 = conn.execute("SELECT username from user where username=?", (at_value,))
                    if cursor2:  # the value behind @ must be someone else
                        # create internal link for @user
                        oldstr = '@' + at_value
                        newstr = "@<a href=\"user.cgi?username=%s\"><b> %s </b></a>" % (at_value, at_value)
                        content = content.replace(oldstr, newstr, 1)
                        # create internal link for @user
                    cursor2.close()
            # create internal link for both other users and me who are being @, for other users, create a link, for myself, just bold it

            # create internal link for # topic, just return back to the original bleat
            p2 = re.compile(r'#([\S]+)')
            at_result = p2.findall(content)  # list : ['DaisyFuentes', 'DaisyFuentes']   at_result is a list contains only one bleat
            for at_value in at_result:
                oldstr = '#' + at_value
                newstr = "<a href=\"search.cgi?user_or_bleat=%23" + at_value + "\"><b>#" + at_value + "</b></a>"
                content = content.replace(oldstr, newstr, 1)
            # create internal link for # topic, just return back to the original bleat

            if other_username == username:
                user_link = "%s %s" % (url_avatar, username)
            else:
                user_link = "<a href=user.cgi?username=%s> %s %s </a>" % (other_username, url_avatar, other_username)
            bleat_detail_link = "<a class=\"btn btn-default\" href=\"detail.cgi?bleatID=%s\" role=\"button\">View details &raquo;</a>" % id
        else:
            user_link = "%s %s" % (url_avatar, other_username)
            bleat_detail_link = "<a class=\"btn btn-default\" href=\"#\" role=\"button\">View details &raquo;</a>"

        html += "<div class=\"col-md-6\">\
                    <h2> %s </h2><p><small>posted at %s</small></p>\
                    <p> %s </p>\
                    <p> %s </p>\
                </div>" % (user_link, date_time, content, bleat_detail_link)
        if block % 2 == 1:
            html += "</div>"
        block += 1
    if block % 2 == 1:
        html += "</div>"
    html += "</div>"
    html += """
    <hr>
    <div class="row">
        <div class="col-md-4 col-md-offset-1">
              <a id="previous" class="btn btn-success" href="?page=%d" role="button">&laquo;Prev Page</a>
        </div>
        <div class="col-md-2"><b style="font-size:large;">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
              Page %d </b>
        </div>
        <div class="col-md-4">
              <a id="next" class="btn btn-success pull-right" href="?page=%d" role="button">Next Page &raquo;</a>
        </div>

    </div>
    <br><br>
    <script type="text/javascript">
        $(function(){
            if( %d <= 0){
                 $("a#previous").click(function(event) {
                   return false;
                 });
            }
            if( %d >= %d){
                 $("a#next").click(function(event) {
                   return false;
                 });
            }
        })
    </script>
    """ % (int(page) - 1, int(page), int(page) + 1, int(page), int(page), number_of_page)

    if cursor:
        cursor.close()
    conn.close()
    return html

def redirect(url):
    return "Location: %s" % url

#
# Show unformatted details for user "n".
# Increment parameter n and store it as a hidden variable
#
def user_page(prompt_login, prompt_logout, parameters):
    global cookie
    global home_latitude_map
    global home_longitude_map
    global flag_activate_account
    global flag_create_account_successfully
    global flag_activate_exception
    global flag_logout
    global flag_post_successfully
    prompt_post_successfully = ""
    if flag_post_successfully == 1:
        prompt_post_successfully = "post successfully !"

    sid = ''
    string_cookie = os.environ.get('HTTP_COOKIE')
    if string_cookie:
        cookie.load(string_cookie)
        if 'sid' in cookie:
            sid = cookie['sid'].value

    if (sid == '' and flag_login_successfully == 0) or flag_logout == 1:  # doesn't login in
        prompt_activate_account = ""
        if flag_activate_account == 1:
            prompt_activate_account = "Thanks for registration, we have sent you a confirmation email, please click the link within the email to activate your account :)"
        prompt_create_account_successfully = ""
        if flag_create_account_successfully == 1:   #be careful whether it should be reset
            prompt_create_account_successfully = "Activate account successfully! Sign in and join us :)"
        prompt_create_account_fail = ""
        if flag_activate_exception == 1:
            prompt_create_account_fail = "Sorry! Activation failed. Please try again"
        prompt_recover_password = ''
        if flag_recover_password == 1:
            prompt_recover_password = "Hi, an email containing your current password has been sent you, please check it"

        conn = sqlite3.connect('users.db')
        cursor = conn.execute("SELECT username, full_name, home_suburb, home_latitude, home_longitude, profile from user")

        attr = ["username", "full_name", "home_suburb", "home_latitude", "home_longitude", "profile"]
        detail_users = []
        coordinates = []
        avatar_to_shows = []
        index = 0
        detail_user = ""
        imageUrl = ""
        user = ""
        for row in cursor:
        #username password email full_name home_suburb home_latitude home_longitude profile
            detail_user = ""
            avatar_user = ""
            index = 0
            coordinate = []
            for item in row:
                #if index == 0:
                #    user = item
                if index == 5:
                    if item:
                        imageUrl = str(item)
                        avatar_to_shows.append(imageUrl)
                    else:
                        imageUrl = "avatar/default.jpg"
                        avatar_to_shows.append(imageUrl)
                    break

                if index == 3:
                    if item:
                        home_latitude_map_tmp = float(item)
                    else:
                        home_latitude_map_tmp = 0.0
                    coordinate.append(home_latitude_map_tmp)
                if index == 4:
                    if item:
                        home_longitude_map_tmp = float(item)
                    else:
                        home_longitude_map_tmp = 0.0
                    coordinate.append(home_longitude_map_tmp)
                    coordinates.append(coordinate)
                if item:
                    detail_user += attr[index] + " : " + str(item) + "<br>"
                    index += 1
                else:
                    index += 1
            detail_user.rstrip("<br>")
            detail_users.append(detail_user)

        n = int(parameters.getvalue('n', 0)) #the second para is the default value to return if the requested key is not present
        avatar_to_show = avatar_to_shows[n % len(avatar_to_shows)]
        user_to_show = detail_users[n % len(detail_users)]
        coordinate_to_show = coordinates[n % len(coordinates)]
        home_latitude_map = coordinate_to_show[0]
        home_longitude_map = coordinate_to_show[1]

        conn.close()
        return """
        <div class="jumbotron narrow">
              <div class="container">
                <h5>%s</h5>
                <h5>%s</h5>
                <h5>%s</h5>
                <h5>%s</h5>
                <h5 style="color:red;font-weight:bold;">%s</h5>
                <h5 style="color:red;font-weight:bold;">%s</h5>
                <h4>Welcome to Bitter! Below is our user list... &nbsp;&nbsp;</h4>

                <div class="col-md-4"><img src="%s"></div>

                <div class="col-md-4">
                %s
                <br><br>
                    <form method="POST" action="">
                        <input type="hidden" name="n" value="%s">
                        <!-- <input type="submit" value="Next user" class="bitter_button"> -->
                        <!-- <p><a class="btn btn-primary btn-lg" type="submit" role="button">Next user &raquo;</a></p> -->
                        <button type="submit" class="btn btn-primary">Next user &raquo;</button>
                    </form>
                </div>

                <div class="col-md-4" id="mapholder"></div>

              </div>
            </div>
        """ % (prompt_recover_password, prompt_activate_account, prompt_create_account_successfully, prompt_create_account_fail, prompt_login, prompt_logout, avatar_to_show, user_to_show, n + 1)

    else:
        if sid == "":
            return """
            <script language"javascript">
                window.location.href="bitter.cgi";
            </script>
            """
        else:
            string_cookie = os.environ.get('HTTP_COOKIE')
            cookie.load(string_cookie)
            username = cookie['sid'].value
            username = sid

            conn = sqlite3.connect('users.db')
            cursor = conn.execute("SELECT username, full_name, home_suburb, home_latitude, home_longitude, profile from USER where username=?", (username,))

            attr = ["username", "full_name", "home_suburb", "home_latitude", "home_longitude"]
            index = 0
            detail_user = ""
            imageUrl = ""
            for row in cursor:
            #username password email full_name home_suburb home_latitude home_longitude profile
                detail_user = ""
                index = 0
                for item in row:
                    if index == 5:
                        if item:
                            imageUrl = str(item)
                        else:
                            imageUrl = "avatar/default.jpg"
                        break
                    if item:
                        if index == 3:
                            home_latitude_map = float(item)
                        if index == 4:
                            home_longitude_map = float(item)
                        detail_user += attr[index] + " : " + str(item) + "<br>"
                        index += 1
                    else:
                        index += 1
                detail_user.rstrip("<br>")

            conn.close()

            post_bleat = """
            <form method="post" action="" class="form-horizontal">
            <fieldset>
                <b style="text-align:center"> %s </b>
                <!-- Textarea -->
                <div class="form-group">
                    <div>
                        <div class="controls">
                            <textarea maxlength="142" placeholder="post bleat here..." class="form-control" rows="6" name="content"></textarea>
                        </div>
                    </div>
                </div>
                <!-- Two text -->
                <div class="form-group">
                    <div class="col-md-6">
                        <label class="sr-only" for="exampleInputAmount">longitude</label>
                        <div class="input-group">
                          <div class="input-group-addon">longitude</div>
                          <input type="text" class="form-control" name="longitude" id="longitude" placeholder="provide if you want">
                        </div>
                    </div>
                    <div class="col-md-6">
                        <label class="sr-only" for="exampleInputAmount">latitude</label>
                        <div class="input-group">
                          <div class="input-group-addon">latitude</div>
                          <input type="text" class="form-control" name="latitude" id="latitude" placeholder="provide if you want">
                        </div>
                    </div>
                </div>
                <!-- upload and submit button -->
                <div class="form-group">
                    <div class="col-sm-6"><input type="file" id="exampleInputFile"></div>
                             <!--   <input class="input-file" id="fileInput" type="file">
                                    <button type="submit" class="btn btn-primary">Next user &raquo;</button>
                                    <input type="file" id="exampleInputFile">
                                    <button type="file" class="btn btn-info pull-left">File</button>
                             -->
                    <div class="col-sm-6"><button type="submit" class="btn btn-primary btn-sm pull-right">Post it!</button></div>
                </div>
            </fieldset>
          </form>
          """ % prompt_post_successfully

            return """
            <div class="jumbotron">
                <div class="container">
                    <div class="col-md-3 image"><img src="%s" class="img-thumbnail"></div>
                    <div class="col-md-6"> %s </div>
                    <div class="col-md-3" id="mapholder"></div>
                </div>
            </div>
            """ % (imageUrl, post_bleat)


#
# HTML placed at the top of every page
#
def page_header():
    global cookie
    global flag_login_successfully
    global flag_logout
    sid = ''
    string_cookie = os.environ.get('HTTP_COOKIE')
    if string_cookie:
        cookie.load(string_cookie)
        if 'sid' in cookie:
            sid = cookie['sid'].value

    if (sid == '' and flag_login_successfully == 0) or flag_logout == 1:  # be careful whether add "or cookie['sid'].value != username"
        reg_icon = """
            <a href="views/register.html">Register</a>
            <li><a href="views/password_recovery.html">Forget Password?</a></li>
         """
        login_or_profile = """
        <form class="navbar-form navbar-right" method="post" action="./bitter.cgi">
        <input type="hidden" name="login" value="login" />
        <div class="form-group">
          <input type="text" placeholder="Username" name="username" class="form-control">
        </div>
        <div class="form-group">
          <input type="password" placeholder="Password" name="password" class="form-control">
        </div>
        <button type="submit" class="btn btn-success">Sign in</button>
        </form>
        """

        login_nav = ""
        login_search = ""
        logout_icon = ""

    else:
        reg_icon = ""
        login_or_profile = ""
        login_nav = """
        <li> <a href="setting.cgi">Profile</a> </li>
        <li> <a href="bleat.cgi">Bleats</a> </li>
        <li> <a href="friend.cgi">Friends</a> </li>

        <li> <a href="relate.cgi">@Related</a> </li>
        <li> <a href="participate.cgi">Participated</a> </li>
        <li> <a href="comment.cgi">My Commented Posts</a> </li>
        """

        login_search = """
        <form method="get" action="search.cgi" class="navbar-form navbar-left" role="search">
            <div class="form-group">
                <input type="text" name="user_or_bleat" class="form-control" placeholder="Search User Or Bleat">
            </div>
            <button type="submit" class="btn btn-default">Search</button>
        </form>
        """
        logout_icon = "<li><a href=\"?action=logout\">Logout</a></li>"

    #should has an empty line below.
    return """Content-Type: text/html

    <!DOCTYPE html>
    <html lang="en">
    <head>
    <title>Bitter</title>
    <script src="javascripts/jquery-2.1.4.min.js"></script>
    <script src="javascripts/bootstrap.min.js"></script>
    <link rel='stylesheet' href='stylesheets/bitter.css' />
    <link rel='stylesheet' href='stylesheets/bootstrap.min.css' />
    <link rel='stylesheet' href='stylesheets/bootstrap-responsive.min.css' />
    </head>
    <body>

    <nav class="navbar navbar-inverse navbar-fixed-top">
      <div class="container">
        <div class="navbar-header">
          <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#navbar" aria-expanded="false" aria-controls="navbar">
            <span class="sr-only">Toggle navigation</span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </button>
          <a class="navbar-brand" href="#">Bitter</a>
        </div>
        <div id="navbar" class="navbar-collapse collapse">
            <ul class="nav navbar-nav navbar-left">
                <li><a href="./bitter.cgi">Home</a></li>
                <li> %s </li>
                <li> %s </li>
            </ul>
            %s
            <ul class="nav navbar-nav navbar-right">
               %s
               <li><a href="views/about.html">About</a></li>
           </ul>
           %s
        </div><!--/.navbar-collapse -->
      </div>
    </nav>
    """ % (reg_icon, login_nav, login_search, logout_icon, login_or_profile)
#<!-- <p>sid is:%s</p><br><p>flag_login_successfully is:%d</p><br><p>string_cookie is: %s<p> -->
#sid, flag_login_successfully, string_cookie


#
# HTML placed at the bottom of every page
# It includes all supplied parameter values as a HTML comment
# if global variable debug is set
#
def page_trailer(parameters):
    global home_latitude_map
    global home_longitude_map
    html = ""
    if home_latitude_map != 0.0 and home_longitude_map != 0.0:
        html = """
        <script>
        var x = document.getElementById("mapholder");
        function getLocation() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(showPosition, showError);
            } else {
                x.innerHTML = "Geolocation is not supported by this browser.";
            }
        }
        function showPosition(position) {
            var latlon = %f + "," + %f;
            var img_url = "http://maps.googleapis.com/maps/api/staticmap?center="
            +latlon+"&zoom=13&size=300x240&sensor=false";
            document.getElementById("mapholder").innerHTML = "<img src='"+img_url+"'>";
        }
        function showError(error) {
            switch(error.code) {
                case error.PERMISSION_DENIED:
                    x.innerHTML = "User denied the request for Geolocation."
                    break;
                case error.POSITION_UNAVAILABLE:
                    x.innerHTML = "Location information is unavailable."
                    break;
                case error.TIMEOUT:
                    x.innerHTML = "The request to get user location timed out."
                    break;
                case error.UNKNOWN_ERROR:
                    x.innerHTML = "An unknown error occurred."
                    break;
            }
        }
        window.onload = getLocation;
        </script>
        """ % (home_latitude_map, home_longitude_map)
    else:
        html = """
        <script>
        var x = document.getElementById("mapholder");

        function getLocation() {
            x.innerHTML = "";
        }
        window.onload = getLocation;
        </script>
        """

    if debug:
        html += "".join("<!-- %s=%s -->\n" % (p, parameters.getvalue(p)) for p in parameters)
    html += "</body>\n</html>"
    return html

if __name__ == '__main__':
    cookie = Cookie.SimpleCookie()
    debug = 1
    flag_activate_account = 0
    flag_activate_exception = 0
    flag_create_account_successfully = 0
    flag_login_successfully = 0
    flag_logout = 0
    flag_post_successfully = 0
    flag_recover_password = 0
    home_latitude_map = 0.0
    home_longitude_map = 0.0
    main()
