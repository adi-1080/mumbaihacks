const mongoose = require('mongoose');

const uri = 'mongodb+srv://mehtatanay04:tanaymehta15@synapse.wwdu1cz.mongodb.net/medisync?retryWrites=true&w=majority&appName=MedSahay';

mongoose.connect(uri).then(async () => {
  const db = mongoose.connection.db;
  
  // Delete all patients
  const deleteResult = await db.collection('patients').deleteMany({});
  console.log(`Deleted ${deleteResult.deletedCount} patients`);
  
  // Reset queue state
  const updateResult = await db.collection('queuestate').updateOne(
    { type: 'GLOBAL' },
    { 
      $set: { 
        currentTokenNumber: 0,
        'dailyStats.totalBookings': 0,
        'dailyStats.emergencyPatients': 0,
        'currentMetrics.patientsWaiting': 0,
        'currentMetrics.emergencyCount': 0,
        lastMetricsUpdate: new Date(),
        updatedAt: new Date()
      } 
    }
  );
  console.log('Reset queue state');
  
  // Verify
  const queueState = await db.collection('queuestate').findOne({ type: 'GLOBAL' });
  if (queueState) {
    console.log('Current Token Number:', queueState.currentTokenNumber);
  } else {
    console.log('Queue state not found - will be created on first booking');
  }
  
  const patientsCount = await db.collection('patients').countDocuments({});
  console.log('Patients in database:', patientsCount);
  
  console.log('\n✅ MongoDB reset complete! Ready for testing.');
  
  process.exit(0);
}).catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});
