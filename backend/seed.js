require('dotenv').config();
const { initMongoDB, closeMongoDB } = require('./config/mongodb');
const Clinic = require('./schemas/Clinic');
const Doctor = require('./schemas/Doctor');
const logger = require('./config/logger');

/**
 * Seed Script
 * Initializes MongoDB with default clinic and doctors
 */

async function seedDatabase() {
  try {
    logger.info('🌱 Starting database seed...');

    // Connect to MongoDB
    await initMongoDB();

    // Check if clinic already exists
    const existingClinic = await Clinic.findOne();
    if (!existingClinic) {
      // Create default clinic
      const clinic = new Clinic({
        name: process.env.CLINIC_NAME || 'MediSync Health Center',
        address: process.env.CLINIC_ADDRESS || 'Lilavati Hospital, Bandra West, Mumbai, Maharashtra, India',
        location: {
          latitude: parseFloat(process.env.CLINIC_LAT || '19.0560'),
          longitude: parseFloat(process.env.CLINIC_LON || '72.8311'),
        },
        contact: {
          phone: '+91-22-2656-1000',
          email: 'info@medisync.health',
          website: 'https://medisync.health',
        },
        operatingHours: {
          monday: '09:00-18:00',
          tuesday: '09:00-18:00',
          wednesday: '09:00-18:00',
          thursday: '09:00-18:00',
          friday: '09:00-18:00',
          saturday: '09:00-14:00',
          sunday: 'Closed',
        },
        specializations: ['General Medicine', 'Pediatrics', 'Emergency Care', 'Cardiology'],
        facilities: ['24/7 Emergency', 'Pharmacy', 'Laboratory', 'X-Ray', 'ICU'],
        isActive: true,
      });

      await clinic.save();
      logger.info('✅ Default clinic created');
    } else {
      logger.info('ℹ️  Clinic already exists, skipping...');
    }

    // Check if doctors already exist
    const existingDoctors = await Doctor.countDocuments();
    if (existingDoctors === 0) {
      // Create default doctors
      const doctors = [
        {
          doctorId: 'DOC_001',
          name: 'Dr. Rajesh Kumar',
          specialization: 'General Physician',
          qualification: 'MBBS, MD',
          experienceYears: 15,
          contact: {
            phone: '+91-9876543210',
            email: 'rajesh.kumar@medisync.health',
          },
          schedule: new Map([
            ['monday', '09:00-18:00'],
            ['tuesday', '09:00-18:00'],
            ['wednesday', '09:00-18:00'],
            ['thursday', '09:00-18:00'],
            ['friday', '09:00-18:00'],
            ['saturday', '09:00-14:00'],
            ['sunday', 'Off'],
          ]),
          available: true,
          statistics: {
            averageConsultationTime: 15,
          },
          rating: 4.8,
          languages: ['English', 'Hindi', 'Marathi'],
          isActive: true,
        },
        {
          doctorId: 'DOC_002',
          name: 'Dr. Priya Sharma',
          specialization: 'Pediatrician',
          qualification: 'MBBS, MD (Pediatrics)',
          experienceYears: 10,
          contact: {
            phone: '+91-9876543211',
            email: 'priya.sharma@medisync.health',
          },
          schedule: new Map([
            ['monday', '09:00-18:00'],
            ['tuesday', '09:00-18:00'],
            ['wednesday', '09:00-18:00'],
            ['thursday', '09:00-18:00'],
            ['friday', '09:00-18:00'],
            ['saturday', '09:00-14:00'],
            ['sunday', 'Off'],
          ]),
          available: true,
          statistics: {
            averageConsultationTime: 20,
          },
          rating: 4.9,
          languages: ['English', 'Hindi'],
          isActive: true,
        },
        {
          doctorId: 'DOC_003',
          name: 'Dr. Amit Patel',
          specialization: 'Emergency Medicine',
          qualification: 'MBBS, MD (Emergency)',
          experienceYears: 12,
          contact: {
            phone: '+91-9876543212',
            email: 'amit.patel@medisync.health',
          },
          schedule: new Map([
            ['monday', '09:00-18:00'],
            ['tuesday', '09:00-18:00'],
            ['wednesday', '09:00-18:00'],
            ['thursday', '09:00-18:00'],
            ['friday', '09:00-18:00'],
            ['saturday', '09:00-14:00'],
            ['sunday', 'Off'],
          ]),
          available: true,
          statistics: {
            averageConsultationTime: 10,
          },
          rating: 4.7,
          languages: ['English', 'Hindi', 'Gujarati'],
          isActive: true,
        },
      ];

      await Doctor.insertMany(doctors);
      logger.info('✅ Default doctors created (3 doctors)');
    } else {
      logger.info(`ℹ️  ${existingDoctors} doctor(s) already exist, skipping...`);
    }

    logger.info('🎉 Database seeding completed successfully!');
    logger.info('');
    logger.info('Summary:');
    const clinicCount = await Clinic.countDocuments();
    const doctorCount = await Doctor.countDocuments();
    logger.info(`  📋 Clinics: ${clinicCount}`);
    logger.info(`  👨‍⚕️  Doctors: ${doctorCount}`);
    logger.info('');

  } catch (error) {
    logger.error('❌ Error seeding database:', error);
    process.exit(1);
  } finally {
    await closeMongoDB();
    process.exit(0);
  }
}

// Run seed script
seedDatabase();
