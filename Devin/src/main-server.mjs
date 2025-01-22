import express from 'express';
import cors from 'cors';
import mysql from 'mysql2';
import multer from 'multer';
import path from 'path';
import { fileURLToPath } from 'url';

// Server configuration
export const server = express();
const port = process.env.PORT || 3000;
server.use(express.json());
server.use(cors());
server.listen(port, () => {
    console.log(`Server is running on port ${port}`);
});

// File handling with multer
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

server.use('/images', express.static(path.join(__dirname, 'images')));

const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, './images');  // Updated to use relative path
    },
    filename: (req, file, cb) => {
        cb(null, Date.now() + path.extname(file.originalname));  // Rename file with timestamp
    }
});
const upload = multer({ storage: storage });

// Database connection
const db = mysql.createConnection({
    host: 'localhost',
    user: 'root',
    password: '',
    database: 'onlineportfoliodb',
});
db.connect((err) => {
    if (err) {
        console.error('Database is not connected');
        return;
    }
    console.log('Database Connected...');
});
// Create project route
server.post('/create-project', upload.single('projectFilePath'), (req, res) => (!req.body.projectName || !req.file ? res.status(400).json({ message: 'Missing project name or file' }) : db.query('INSERT INTO projects (projectName, projectFilePath) VALUES (?, ?)', [req.body.projectName, req.file.filename], (err) => res.status(err ? 500 : 200).json({ message: err ? 'Server Error' : 'Project Added' }))));
// Update project route
server.put('/update-project/:projectID', upload.single('projectFilePath'), (req, res) => (!req.body.projectName || !req.file ? res.status(400).json({ message: 'Missing project name or file' }) : db.query('UPDATE projects SET projectName = ?, projectFilePath = ? WHERE projectID = ?', [req.body.projectName, req.file.filename, req.params.projectID], (err) => res.status(err ? 500 : 200).json({ message: err ? 'Server Error' : 'Project Updated' }))));
//Delete project route
server.delete('/delete-project/:projectID', (req, res) => (!req.params.projectID ? res.status(400).json({ message: 'Missing project ID' }) : db.query('DELETE FROM projects WHERE projectID = ?', [req.params.projectID], (err) => res.status(err ? 500 : 200).json({ message: err ? 'Server Error' : 'Project Deleted' }))));
//View Prject route
server.get('/view-project/:projectID', (req, res) => req.params.projectID ? db.query('SELECT * FROM projects WHERE projectID = ?', [req.params.projectID], (err, result) => res.status(err ? 500 : result.length ? 200 : 404).json(err ? { message: 'Server Error' } : result.length ? result[0] : { message: 'Project not found' })) : res.status(400).json({ message: 'Missing project ID' }));
//View All projects
server.get('/view-all-projects', (req, res) => db.query('SELECT * FROM projects', (err, result) => res.status(err ? 500 : result.length ? 200 : 404).json(err ? { message: 'Server Error' } : result.length ? result : { message: 'No projects found' })));

