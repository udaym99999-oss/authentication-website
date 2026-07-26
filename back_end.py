from http.server import HTTPServer,BaseHTTPRequestHandler
from pymongo import MongoClient
import json
import uuid
import bcrypt
from multipart import parse_form

client = MongoClient("mongodb://localhost:27017") #connects py to mongodb server

db = client["student_db"]  #collection

collection = db["students"] #document 

sessions = {}


class Myserver(BaseHTTPRequestHandler):
    def do_GET(self):
        print(self.path)

        if self.path =="/profile":
            self.profile()    
        else:
            self.send_response(400)
            self.end_headers()

    def do_POST(self):
        print("POST reached:", self.path)

        if self.path == "/signup":
            self.signup()
        elif self.path == "/login":
            self.login()
        elif self.path == "/logout":
            self.logout()
        elif self.path == "/upload_image":
            self.upload_image()    
        else:
            self.send_response(404)
            self.end_headers() 

    def do_PUT(self):
        #print("POST reached:", self.path)  

        if self.path =="/profile":
            self.update_profile()
        else:
            self.send_response(400)
            self.end_headers()

    def do_DELETE(self):

        if self.path == "/Delete":
            self.delete()
        else:
            self.send_response(400)
            self.end_headers()    
     
    #OPTION Request = permission check request
    def do_OPTIONS(self):
        self.send_response(200)

        self.send_header("Access-Control-Allow-Origin","http://127.0.0.1:5500")
        self.send_header("Access-Control-Allow-Credentials","true")
        self.send_header("Access-Control-Allow-Methods","POST,GET,PUT,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.end_headers()

    def signup(self):
        length = int(self.headers["Content-Length"])  
        data = self.rfile.read(length)
        user = json.loads(data)
        #password hasing
        password = str(user["password"])
        password = password.encode("utf-8")
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password,salt)
        hash_password = hashed_password.decode()
        user["password"] = hash_password

        collection.insert_one(user)
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(b"Signup Success")

    def login(self):
        length = int(self.headers["Content-Length"])  
        data = self.rfile.read(length)    #reads incoming data
        user = json.loads(data)
        password = str(user["password"])

        user = collection.find_one({
            "email":user["email"],
        })

        if user:
            hello = str(user["password"])

        if user and bcrypt.checkpw(password.encode(),
                                   hello.encode()):

            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","http://127.0.0.1:5500")
            self.send_header("Access-Control-Allow-Credentials","true")

            session_id = str(uuid.uuid4())

            sessions[session_id] = {
                "name":user["name"],
               "email":user["email"]
            }

            response = json.dumps({
                "status":"success",
               "name":user["name"],
               "email":user["email"]
            })
            self.send_header(
                "Set-Cookie",
                 f"session={session_id}; Path=/; HttpOnly"
            )

            self.end_headers()

            self.wfile.write(response.encode()) #send the data in encoded through the network
                                                #instead of raw sending data
        else:
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","http://127.0.0.1:5500")
            self.send_header("Access-Control-Allow-Credentials","true")
            self.end_headers()
            response = json.dumps({
                "status":"Failed"
            }) 
            self.wfile.write(response.encode())

    def profile(self):
        """Get current user profile"""
        user = self.get_current_user()
        
        if user:
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","http://127.0.0.1:5500")
            self.send_header("Access-Control-Allow-Credentials","true")
            self.end_headers()
            
            response = json.dumps({
                "status":"success",
                "name":user["name"],
                "email":user["email"]
            })
            self.wfile.write(response.encode())
        else:
            self.send_response(401)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","http://127.0.0.1:5500")
            self.send_header("Access-Control-Allow-Credentials","true")
            self.end_headers()
            
            response = json.dumps({
                "status":"Failed",
                "message":"No active session"
            })
            self.wfile.write(response.encode())


    def logout(self):
        cookie = self.headers.get("Cookie")
        self.send_response(200)
        session_id = self.headers.get("Cookie").split("=")[1]
        self.send_header(
                "Set-Cookie",
                 f"session=; Path=/; Max-Age=0; HttpOnly"
        )
        if session_id in sessions:
            del sessions[session_id]

        print("Cookie session id:", session_id)
        print("Current sessions:", sessions)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","http://127.0.0.1:5500")
        self.send_header("Access-Control-Allow-Credentials","true")
        self.end_headers()

        response = json.dumps({
            "status":"success"
        })
        self.wfile.write(response.encode())

    def get_current_user(self):
        """Helper method that returns user data from session without sending HTTP responses"""
        cookie = self.headers.get("Cookie")
        
        # Check for cookie FIRST before processing
        if not cookie:
            return None
        
        # Parse session ID from cookie
        sessions_id = cookie.split("=")[1] 
        user = sessions.get(sessions_id)
        
        return user    

    def upload_image(self):

        print("all headers:",self.headers)
        print("content_type:",self.headers.get("Content-Type"))
        print("content_length",self.headers.get("Content-Length"))

        def on_field(field):
            print("Normal field recived:",field)

        def on_files(file):
            print("file recived:",file)
            print("file name:",file.file_name)

        headers = {
            "Content-Type":self.headers["Content-Type"].encode(),
            "Content-Length":self.headers["Content-Length"].encode()
        }

        parse_form(
            headers,
            self.rfile,
            on_field,
            on_files,
        )

        self.send_response(200)
        self.send_header("Content-Type","text/plain")
        self.send_header("Access-Control-Allow-Origin","http://127.0.0.1:5500")
        self.send_header("Access-Control-Allow-Credentials","true")
        self.end_headers()
        self.wfile.write(b"the uploaded file is successfully reached")  

    def update_profile(self):
        length = int(self.headers["Content-Length"])
        data = self.rfile.read(length)
        new_data = json.loads(data)
        session_id = self.headers.get("Cookie").split("=")[1]

        current_data = self.get_current_user()
        
        # Validate user is authenticated
        if not current_data:
            self.send_response(401)
            self.send_header("Content-Type","application/json")
            self.send_header("Access-Control-Allow-Origin","http://127.0.0.1:5500")
            self.send_header("Access-Control-Allow-Credentials","true")
            self.end_headers()
            response = json.dumps({"status":"Failed", "message":"Unauthorized"})
            self.wfile.write(response.encode())
            return

        collection.update_one(
            {
                "name":current_data["name"],
                "email":current_data["email"]
            },
            {
                "$set": {
                    "name":new_data["name"],
                    "email":new_data["email"]
                }
            }
        )
        # Store updated data as a dict (not separate values)
        sessions[session_id] = {
            "name": new_data["name"],
            "email": new_data["email"]
        }

        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","http://127.0.0.1:5500")
        self.send_header("Access-Control-Allow-Credentials","true")
        self.end_headers()
        response = json.dumps({"status":"success", "message":"Profile updated successfully"})
        self.wfile.write(response.encode())  

    def delete(self):

        current_user = self.get_current_user()

        #Account delete from database(mongodb)
        collection.delete_one({
            "email":current_user["email"]
        })

        #Session will delete in server
        session_id = self.headers.get("cookie").split("=")[1]
        del sessions[session_id]   

        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Access-Control-Allow-Origin","http://127.0.0.1:5500")
        self.send_header("Access-Control-Allow-Credentials","true")
        self.end_headers()
        responses = json.dumps({
            "status":"success"
        })
        self.wfile.write(responses.encode())


        

        



server = HTTPServer(("localhost",8000),Myserver)  
print("server is runnig....")
server.serve_forever()   #server stays for ever. means when run the program
