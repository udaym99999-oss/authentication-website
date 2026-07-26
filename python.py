import bcrypt

password = "uday143".encode()

salt = bcrypt.gensalt()

hashed_password = bcrypt.hashpw(password,salt)


print(password)
print(salt)
print(hashed_password)

