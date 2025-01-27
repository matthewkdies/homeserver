const http = require('http');

const options = {
    hostname: 'localhost',
    port: 5006,
    path: '/',
    method: 'GET',
};

const req = http.request(options, (res) => {
    if (res.statusCode === 200) {
        console.log('Health check passed');
    } else {
        console.error(`Health check failed with status code ${res.statusCode}`);
        process.exit(1);
    }
});

req.on('error', (error) => {
    console.error('Health check failed:', error);
    process.exit(1);
});

req.end();
