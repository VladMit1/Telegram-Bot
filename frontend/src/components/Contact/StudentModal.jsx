import { motion, AnimatePresence } from 'framer-motion';
import {
   X,
   GraduationCap,
   PlusCircle,
   Settings,
   Check,
   Calendar as CalendarIcon,
} from 'lucide-react';
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
   const [updateContact] = useUpdateProgressMutation();

   // Состояния
   const [currentMonth, setCurrentMonth] = useState(moment());
   const [isPayMode, setIsPayMode] = useState(false);

   // Поля для новой оплаты
   const [payAmount, setPayAmount] = useState(student.lesson_price || 500);
   const [payDate, setPayDate] = useState(moment().format('YYYY-MM-DD'));

   const lessonPrice = student.lesson_price || 500;
   const totalPaid = student.total_paid || 0;

   // 1. Расчет истории с учетом оплаты (сквозной баланс)
   const studentHistory = useMemo(() => {
      const sorted = allLessons
         .filter((l) => String(l.student_id) === String(student.id))
         .sort((a, b) => {
            const dtA = `${a.lesson_date} ${a.lesson_time || '00:00'}`;
            const dtB = `${b.lesson_date} ${b.lesson_time || '00:00'}`;
            return dtA.localeCompare(dtB);
         });

      return sorted.map((lesson, index) => {
         const costUntilNow = (index + 1) * lessonPrice;
         return {
            ...lesson,
            date: lesson.lesson_date,
            is_paid: totalPaid >= costUntilNow,
         };
      });
   }, [allLessons, student.id, totalPaid, lessonPrice]);

   // 2. Статистика
   const currentBalance = totalPaid - studentHistory.length * lessonPrice;
   const lessonsLeft = Math.floor(currentBalance / lessonPrice);

   const lessonsThisMonth = useMemo(() => {
      return studentHistory.filter(
         (l) =>
            moment(l.date).isSame(currentMonth, 'month') &&
            moment(l.date).isSame(currentMonth, 'year')
      );
   }, [studentHistory, currentMonth]);

   // Хендлеры
   const handleConfirmPayment = async () => {
      if (payAmount && !isNaN(payAmount)) {
         const newTotal = totalPaid + Number(payAmount);
         try {
            await updateContact({
               id: student.id,
               total_paid: newTotal,
               // payDate можно сохранять отдельно, если в БД есть таблица платежей
            }).unwrap();
            setIsPayMode(false);
         } catch (e) {
            alert('Ошибка при сохранении');
         }
      }
   };

   const handleChangePrice = async () => {
      const newPrice = prompt('Цена за 1 урок (PLN):', lessonPrice);
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

               <AnimatePresence mode="wait">
                  {isPayMode ? (
                     <motion.div
                        className="payment-form-container"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                     >
                        <div className="payment-form-inputs">
                           <div className="input-box">
                              <label>Сумма (PLN)</label>
                              <input
                                 type="number"
                                 value={payAmount}
                                 onChange={(e) => setPayAmount(e.target.value)}
                              />
                           </div>
                           <div className="input-box">
                              <label>Дата оплаты</label>
                              <input
                                 type="date"
                                 value={payDate}
                                 onChange={(e) => setPayDate(e.target.value)}
                              />
                           </div>
                        </div>
                        <div className="payment-form-actions">
                           <button
                              className="btn-cancel"
                              onClick={() => setIsPayMode(false)}
                           >
                              Отмена
                           </button>
                           <button
                              className="btn-confirm"
                              onClick={handleConfirmPayment}
                           >
                              <Check size={16} /> Подтвердить
                           </button>
                        </div>
                     </motion.div>
                  ) : (
                     <div className="action-buttons">
                        <button
                           className="payment-btn"
                           onClick={() => setIsPayMode(true)}
                        >
                           <PlusCircle size={18} /> Внести оплату
                        </button>
                        <button
                           className="price-btn"
                           onClick={handleChangePrice}
                        >
                           <Settings size={18} /> Цена: {lessonPrice}₽
                        </button>
                     </div>
                  )}
               </AnimatePresence>

               <div className="stats-row">
                  <div className="stat-box">
                     <span
                        className="num"
                        style={{
                           color: currentBalance < 0 ? '#ff4d4f' : '#52c41a',
                        }}
                     >
                        {currentBalance} PLN
                     </span>
                     <span className="txt">Баланс</span>
                  </div>
                  <div className="stat-box">
                     <span className="num">
                        {lessonsLeft > 0 ? lessonsLeft : 0}
                     </span>
                     <span className="txt">Запас уроков</span>
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
