import { motion } from 'framer-motion';
import { BookOpen, CalendarPlus, UserPlus, Calendar } from 'lucide-react';
import moment from 'moment';

export const StudentCard = ({ student, onOpen, onSchedule }) => {
   const currentDay = moment().date();
   const lessonPrice = student.lesson_price || 500;
   const totalPaid = student.total_paid || 0;

   // Считаем количество проведенных уроков для этого студента
   // Если уроки приходят в объекте студента как attended_lessons:
   const attendedCount = (student.attended_lessons || []).length;

   // Либо, если ты берешь их из общего стора lessons:
   // const attendedCount = allLessons.filter(l => l.student_id === student.id).length;

   const balance = totalPaid - attendedCount * lessonPrice;

   // Определяем статус для класса
   const balanceStatus = balance < 0 ? 'negative' : 'positive';
   return (
      <motion.div
         className={`student-card-v2 ${balanceStatus}`}
         whileTap={{ scale: 0.98 }}
         onClick={() => onOpen(student)}
      >
         <div className="card-top">
            <div className="avatar">
               {student.photo_url ? (
                  <img
                     src={student.photo_url}
                     referrerPolicy="no-referrer"
                     loading="lazy"
                     alt={student.name}
                     style={{
                        width: '100%',
                        height: '100%',
                        borderRadius: '50%',
                        objectFit: 'cover',
                     }}
                  />
               ) : (
                  student.name.charAt(0).toUpperCase()
               )}
            </div>

            <div className="main-info">
               <h3>{student.name}</h3>
               <div className="sub-info">
                  <UserPlus size={12} />
                  <span>В базе с {student.created_at || '—'}</span>
               </div>
            </div>

            <div className="current-date-badge">
               <Calendar
                  size={32}
                  strokeWidth={1.5}
                  className="calendar-icon"
               />
               <span className="day-number">{currentDay}</span>
            </div>
         </div>

         <div className="card-middle">
            <div className="progress-info">
               <BookOpen size={14} />
               <span>
                  {student.last_book || 'Без книги'}: стр.{' '}
                  {student.last_page || 0}
               </span>
            </div>
         </div>

         <div className="card-footer">
            <button
               className="btn-schedule"
               onClick={(e) => {
                  e.stopPropagation();
                  onSchedule(student);
               }}
            >
               <CalendarPlus size={16} />
               <span>Запланировать занятие</span>
            </button>
         </div>
      </motion.div>
   );
};
