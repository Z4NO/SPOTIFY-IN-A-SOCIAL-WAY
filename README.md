## Project Overview

This project originated as an idea to implement the **Spotify API** in external applications that are neither web-based nor desktop-based. The challenge was that users would not be able to authenticate due to the lack of an embedded browser in such applications. 

To address this, the project uses a **web-based backend** to handle the **OAuth2 authentication flow**. Users authenticate through a web interface, and the backend securely manages the **access and refresh tokens**, which are then used to interact with the **Spotify API** on behalf of the user. This approach ensures compatibility with platforms like **Discord** or other similar applications.

### Example Use Case

An example use case is creating a **Discord bot** that interacts with this web backend. The bot can leverage the backend to perform various Spotify-related operations, such as:
- Managing playlists
- Adding songs to the queue
- Sharing music with others

This design enables applications without embedded browsers to provide seamless **Spotify integration**, making music a more social and interactive experience.

---

## Learning and Development

Additionally, this project served as a **personal development opportunity** to deepen knowledge of technologies such as **Python, Firebase, and Flask**. Through this project, the following skills were acquired:

- **OAuth2 Authentication**: Implementing secure authentication flows for third-party APIs.
- **Backend Development**: Building a scalable and modular backend using Flask and Blueprints.
- **Database Management**: Using Firebase to store user data, such as collaborative playlists and session tokens.
- **API Integration**: Interacting with the Spotify API to perform operations like playlist management, song recommendations, and user data retrieval.

By combining **technical challenges** with **creative features**, this project not only solves a practical problem but also transforms music into a **more interactive and community-driven experience**.

---

## Features

### **User Authentication**
- Secure **OAuth2 authentication flow** with Spotify.
- Token management for **access and refresh tokens**.

### **Playlist Management**
- Retrieve user playlists.
- Create new playlists (**public, private, or collaborative**).
- Add songs to playlists.

### **Song Queue Management**
- Add songs to the playback queue.
- Add songs from the same artist as the currently playing track.

### **Collaborative Playlists**
- Check if a user has **collaborative playlists**.
- Add collaborative playlists to the database.

### **Song Search**
- Search for songs by **name and artist** using the Spotify API.

### **Integration with External Platforms**
- Designed to work with platforms like **Discord**, enabling bots to interact with Spotify through the backend.

---

## Technologies Used

- **Python**: Core programming language for backend development.
- **Flask**: Web framework for building the backend and handling routes.
- **Firebase**: Database for storing user data, playlists.
- **Spotify API**: For interacting with Spotify's services.
- **OAuth2**: Authentication protocol for secure user login.
- **Cryptography**: For encrypting sensitive data like tokens.
- **HTML/CSS/JavaScript**: For the web interface.

---

## Installation and Setup

### **Clone the Repository:**
```bash
git clone https://github.com/your-repo/spotify-backend.git
cd spotify-backend
```

### **Install Dependencies:**
Ensure you have Python installed. Then, install the required packages:
```bash
pip install -r requirements.txt
```

### **Set Up Environment Variables:**
Create a `.env` file in the root directory and add the following:
```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:5000/callback
```

### **Run the Application:**
Start the Flask server:
```bash
flask run
```

### **Access the Application:**
Open your browser and navigate to:
```
http://localhost:5000
```

---

## Example Use Case

A **Discord bot** can use this backend to:
- **Authenticate users** with Spotify.
- Retrieve and display their **top tracks or playlists**.
- Add songs to a **shared playlist or queue**.
- Enable **collaborative playlist creation and management**.

---

This project bridges the gap between **Spotify and external applications**, making music more accessible and interactive for users across various platforms.
This allows Discord users to share and interact with music seamlessly, enhancing the social experience.
