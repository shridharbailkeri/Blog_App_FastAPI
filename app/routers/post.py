from fastapi import Body, FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas, oauth2
from ..database import get_db
from sqlalchemy import func

router = APIRouter(
    prefix="/posts",
    tags=['Posts']
)
# http://127.0.0.1:8000/posts?limit=2&skip=3&search=hello%20update
#http://127.0.0.1:8000/posts?search=hello%20up
# %20 is like space 
# when you want info from 2 different db tables you use joins 
# when querying a post, you want the whole details of post's owner, means two tables are invloved posts and user / owner
# # https://www.postgresqltutorial.com/
# # select * from posts LEFT JOIN users ON posts.owner_id = users.id; 
# posts LEFT JOIN users here the first mentioned table posts is the left table and second mentioned table users is right table
# select title, content, email from posts LEFT JOIN users ON posts.owner_id = users.id; 
# select posts.title, posts.content, users.email from posts LEFT JOIN users ON posts.owner_id = users.id; 
# select posts.*, users.email from posts LEFT JOIN users ON posts.owner_id = users.id;
# get the number of posts by each user 
# select users.id, users.email, COUNT(*) from posts LEFT JOIN users ON posts.owner_id = users.id group by users.id;
# be carefull COUNT(*) * counts even null entries means even if posts are 0 u get 1 as result 
#select users.id, users.email, COUNT(posts.id) from posts RIGHT JOIN users ON posts.owner_id = users.id group by users.id;
# instead choose any column from posts table here posts.id to get exact results
# if you want users with null and non null posts also then choose right join as users is right table
# if you want all entries null and non null in posts then choose left column as posts is left table
# select users.id, users.email, COUNT(posts.id) as user_post_count from posts RIGHT JOIN users ON posts.owner_id = users.id group by users.id;
# select * from posts LEFT JOIN votes ON posts.id = votes.post_id; 
#  count number of votes for each and every post group by posts.id
# # select posts.id, COUNT(votes.post_id) from posts LEFT JOIN votes ON posts.id = votes.post_id group by posts.id; 
# select posts.*, COUNT(votes.post_id) as likes from posts LEFT JOIN votes ON posts.id = votes.post_id group by posts.id;
# individual posts
# select posts.*, COUNT(votes.post_id) as likes from posts LEFT JOIN votes ON posts.id = votes.post_id where posts.id=9 group by posts.id;  
@router.get("/", response_model=List[schemas.PostVotes])
#@router.get("/")
def get_posts(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user), 
              limit: int = 10, skip: int = 0, search: Optional[str] = ""):
    #current_user: int is specified as int but oauth2.get_current_user returns user, but it does not matter 
    # int does not break the code 
    #cursor.execute("""SELECT * FROM posts""")
    #posts = cursor.fetchall()
    #posts = db.query(models.Post).filter(models.Post.title.contains(search)).limit(limit).offset(skip).all()
    # get post of logged in user only
    # posts = db.query(models.Post).filter(models.Post.owner_id == current_user.id).all()
    # default in sql alchemy is left join
    # select posts.*, COUNT(votes.post_id) as likes from posts LEFT JOIN votes ON posts.id = votes.post_id group by posts.id;
    results = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(
        models.Vote, models.Vote.post_id == models.Post.id, isouter=True).group_by(models.Post.id).all()
    
    
    return results
#user_id: int = Depends(oauth2.get_current_user())
# get_current_user() function is now going to be a dependency and this is what forces the users to have to be logged in 
# before they can create posts
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.PostResponse)
def create_posts(payLoad: schemas.PostCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    #cursor.execute("""INSERT INTO posts (title, content, published) VALUES (%s, %s, %s) RETURNING *""", (payLoad.title,
    #payLoad.content, payLoad.published))
    #new_post = cursor.fetchone()
    #conn.commit()
    #payLoad.dict() # ** means unpacking the dictionary, to avoid 
    print(current_user.email)
    new_post = models.Post(owner_id=current_user.id, **payLoad.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post) # replace command for RETURNING * in native sql query , retrieve
    return new_post        

# title str, content str 
# {id} path parameter
@router.get("/{id}", response_model=schemas.PostVotes)
def get_post(id: int, response: Response, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    #cursor.execute("""SELECT * FROM posts WHERE ID = %s""", (str(id),))
    #test_post = cursor.fetchone()
    #post = find_post(id)
    #test_post = db.query(models.Post).filter(models.Post.id == id).first()
    result = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(
        models.Vote, models.Vote.post_id == models.Post.id, isouter=True).group_by(models.Post.id).filter(models.Post.id == id).first()
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} was not found")
    
    # check if user who is logged in owns this post 
    #if test_post.owner_id != current_user.id:
    #    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform requested action")
        #response.status_code = status.HTTP_404_NOT_FOUND
        #return {"message": f"post with id: {id} was not found"}
    return result
#status.HTTP_204_NO_CONTENT is you use this you cant send any data back you can send only Response(status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    #cursor.execute("""DELETE FROM posts WHERE id = %s RETURNING *""", (str(id),))
    #deleted_post = cursor.fetchone()
    #conn.commit()
    # we define query here
    post_query = db.query(models.Post).filter(models.Post.id == id)
    # we find the post 
    deleted_post = post_query.first()
    # check if its not there
    if deleted_post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"post with id: {id} doesnot exist")
    # check if user who is logged in owns this post 
    if deleted_post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform requested action")
    
    # grab the original query then we append a delete to delete it thats all
    post_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
    
@router.put("/{id}", response_model=schemas.PostResponse)
def update_post(id: int, updated_post: schemas.PostCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    #cursor.execute("""UPDATE posts SET title = %s, content = %s, published = %s WHERE id = %s RETURNING *""", (post.title,
    #post.content, post.published, str(id)))
    #updated_post = cursor.fetchone()
    #conn.commit()
    # set up a query to find post with specific id 
    post_query = db.query(models.Post).filter(models.Post.id == id)
    # grab that specific post from db
    old_post = post_query.first() # gets from db now
    if old_post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"post with id: {id} doesnot exist")
    
    if old_post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to perform requested action")
    
    post_query.update(updated_post.dict(), synchronize_session=False)
    db.commit()
    return post_query.first()