body {
    font-family: Arial, sans-serif;
    margin: 0;
    background: #f3f5f8;
    color: #1f2937;
}

.container {
    max-width: 1100px;
    margin: 32px auto;
    padding: 0 16px;
}

header {
    margin-bottom: 24px;
}

.panel {
    background: white;
    border-radius: 10px;
    padding: 18px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    margin-bottom: 18px;
}

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
}

label {
    display: block;
    font-weight: 600;
    margin-bottom: 10px;
}

input, select, button {
    width: 100%;
    padding: 10px 12px;
    border-radius: 8px;
    border: 1px solid #d1d5db;
    box-sizing: border-box;
    margin-top: 6px;
}

button {
    background: #2563eb;
    color: white;
    border: none;
    cursor: pointer;
    font-weight: 600;
    margin-top: 12px;
}

button:hover {
    background: #1d4ed8;
}

.message {
    margin-top: 12px;
    font-weight: 600;
}

.success {
    color: #166534;
}

.error {
    color: #b91c1c;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th, td {
    padding: 10px 8px;
    border-bottom: 1px solid #e5e7eb;
    text-align: left;
}
