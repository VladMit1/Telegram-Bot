import { motion } from 'framer-motion';
import { BookOpen, CalendarPlus, UserPlus, Calendar } from 'lucide-react';
import moment from 'moment';
import { useGetLessonsQuery } from '../../store/apiSlice';

export const StudentCard = ({ student, onOpen, onSchedule }) => {
   const { data: allLessons = [] } = useGetLessonsQuery();
   const currentDay = moment().date();
   const todayStr = moment().format('YYYY-MM-DD');
   const price = Number(student.lesson_price) || 0;
   const paid = Number(student.total_paid) || 0;

   // 1. Считаем проведенные уроки (<= сегодня)
   const conductedCount = allLessons.filter(
      (l) =>
         String(l.student_id) === String(student.id) &&
         l.lesson_date <= todayStr
   ).length;

   // 2. Считаем будущие уроки (> сегодня)
   const futureCount = allLessons.filter(
      (l) =>
         String(l.student_id) === String(student.id) && l.lesson_date > todayStr
   ).length;

   const currentBalance = paid - conductedCount * price;

   // ОПРЕДЕЛЯЕМ СТАТУС
   let balanceStatus = 'positive';

   if (currentBalance < 0) {
      // 1. Если баланс уже отрицательный — КРАСНЫЙ (Долг)
      balanceStatus = 'negative';
   } else if (currentBalance < price && futureCount > 0) {
      // 2. Если денег меньше, чем стоит 1 урок, И есть занятия впереди — ОРАНЖЕВЫЙ (Варнинг)
      // Сюда попадет и баланс 0, если запланированы уроки.
      balanceStatus = 'warning';
   } else if (currentBalance === 0 && futureCount === 0) {
      // 3. Если баланс 0 и ничего не запланировано — можно оставить нейтральным или оранжевым
      balanceStatus = 'neutral';
   }
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
