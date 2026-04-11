import { motion } from 'framer-motion';
import { BookOpen, CalendarPlus, UserPlus, Calendar } from 'lucide-react';
import moment from 'moment';

export const StudentCard = ({ student, onOpen, onSchedule }) => {
   const currentDay = moment().date();

   return (
      <motion.div
         className="student-card-v2"
         whileTap={{ scale: 0.98 }}
         onClick={() => onOpen(student)}
      >
         <div className="card-top">
            <div className="avatar">
               {student.name ? student.name.charAt(0).toUpperCase() : '?'}
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
