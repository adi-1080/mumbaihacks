require('dotenv').config();
const mongoose = require('mongoose');

mongoose.connect(process.env.MONGODB_URI).then(async () => {
  const result = await mongoose.connection.db.collection('patients').updateOne(
    {tokenNumber: 2},
    {$set: {status: 'COMPLETED', isActive: false, completedAt: new Date()}}
  );
  console.log('Patient #2 (Amit Kumar - EMERGENCY) marked as COMPLETED');
  console.log('Modified:', result.modifiedCount, 'document(s)');
  process.exit(0);
});
