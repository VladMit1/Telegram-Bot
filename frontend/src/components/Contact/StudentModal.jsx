import { motion } from 'framer-motion';
import { X, GraduationCap, PlusCircle, Settings } from 'lucide-react';
import { StudentCalendar } from './components/StudentCalendar';
import { ProgressBlock } from './components/ProgressBlock';
import { useMemo, useState } from 'react';
import {
   useGetLessonsQuery,
   useUpdateProgressMutation,
} from '../../store/apiSlice';
import moment from 'moment';

export const StudentModal = ({ student, onClose }) => {
   const { data: allLessons = [] } = useGetLessonsQuery();
   const [currentMonth, setCurrentMonth] = useState(moment());
   const [updateContact] = useUpdateProgressMutation();

   // Данные из БД (с дефолтными значениями, если в БД пусто)
   const lessonPrice = student.lesson_price || 500;
   const totalPaid = student.total_paid || 0;

   // 1. УМНЫЙ РАСЧЕТ ИСТОРИИ (с учетом оплаты)
   const studentHistory = useMemo(() => {
      // Сначала фильтруем и сортируем ВСЕ уроки по дате и времени
      const sorted = allLessons
         .filter((lesson) => String(lesson.student_id) === String(student.id))
         .sort((a, b) => {
            const dtA = `${a.lesson_date} ${a.lesson_time || '00:00'}`;
            const dtB = `${b.lesson_date} ${b.lesson_time || '00:00'}`;
            return dtA.localeCompare(dtB);
         });

      // Проходимся по списку и смотрим, на какой урок хватило денег из "котла"
      return sorted.map((lesson, index) => {
         const costUntilNow = (index + 1) * lessonPrice;
         const isPaid = totalPaid >= costUntilNow;

         return {
            ...lesson,
            date: lesson.lesson_date,
            is_paid: isPaid, // Это поле будет использовать календарь для цвета
         };
      });
   }, [allLessons, student.id, totalPaid, lessonPrice]);

   // 2. Расчет баланса и статистики
   const totalLessonsCount = studentHistory.length;
   const currentBalance = totalPaid - totalLessonsCount * lessonPrice;
   const lessonsLeft = Math.floor(currentBalance / lessonPrice);

   const lessonsThisMonth = useMemo(() => {
      return studentHistory.filter(
         (lesson) =>
            moment(lesson.date).isSame(currentMonth, 'month') &&
            moment(lesson.date).isSame(currentMonth, 'year')
      );
   }, [studentHistory, currentMonth]);

   // Хендлеры для кнопок
   const handleAddPayment = async () => {
      const amount = prompt('Введите сумму пополнения (₽):');
      if (amount && !isNaN(amount)) {
         const newTotal = totalPaid + Number(amount);
         try {
            await updateContact({
               id: student.id,
               total_paid: newTotal,
            }).unwrap();
         } catch (e) {
            alert('Ошибка сохранения');
         }
      }
   };

   const handleChangePrice = async () => {
      const newPrice = prompt('Цена за 1 урок (₽):', lessonPrice);
      if (newPrice && !isNaN(newPrice)) {
         await updateContact({
            id: student.id,
            lesson_price: Number(newPrice),
         });
      }
   };

   return (
      <div className="modal-overlay" onClick={onClose}>
         <motion.div
            className="student-modal"
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            onClick={(e) => e.stopPropagation()}
         >
            <div className="modal-handle" />

            <header className="modal-header">
               <div className="title">
                  <GraduationCap size={24} />
                  <h2>{student.name}</h2>
               </div>
               <button className="close-btn" onClick={onClose}>
                  <X />
               </button>
            </header>

            <div className="modal-body">
               <StudentCalendar
                  attendedDays={studentHistory}
                  viewDate={currentMonth}
                  setViewDate={setCurrentMonth}
               />

               <div className="action-buttons">
                  <button className="payment-btn" onClick={handleAddPayment}>
                     <PlusCircle size={18} /> Внести оплату
                  </button>
                  <button className="price-btn" onClick={handleChangePrice}>
                     <Settings size={18} /> Цена: {lessonPrice}₽
                  </button>
               </div>

               <div className="stats-row">
                  <div className="stat-box">
                     <span
                        className="num"
                        style={{
                           color: currentBalance < 0 ? '#ff4d4f' : '#52c41a',
                        }}
                     >
                        {currentBalance} ₽
                     </span>
                     <span className="txt">Баланс</span>
                  </div>
                  <div className="stat-box">
                     <span className="num">
                        {lessonsLeft > 0 ? lessonsLeft : 0}
                     </span>
                     <span className="txt">Осталось уроков</span>
                  </div>
                  <div className="stat-box">
                     <span className="num">{lessonsThisMonth.length}</span>
                     <span className="txt">{currentMonth.format('MMM')}</span>
                  </div>
               </div>

               <ProgressBlock student={student} />
            </div>
         </motion.div>
      </div>
   );
};
