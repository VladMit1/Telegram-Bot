import { motion } from 'framer-motion';
import { X, GraduationCap } from 'lucide-react';
import { StudentCalendar } from './components/StudentCalendar';
import { ProgressBlock } from './components/ProgressBlock';
import { useMemo, useState } from 'react';
import { useGetLessonsQuery, useGetContactsQuery } from '../../store/apiSlice';
import moment from 'moment';
import { PaymentBlock } from './components/PaymentBlok';

export const StudentModal = ({ student: initialStudent, onClose }) => {
   const { data: allLessons = [] } = useGetLessonsQuery();
   const { data: allStudents = [] } = useGetContactsQuery();
   const todayStr = moment().format('YYYY-MM-DD');

   // Получаем актуальные данные из Redux
   const student = useMemo(
      () =>
         allStudents.find((s) => s.id === initialStudent.id) || initialStudent,
      [allStudents, initialStudent]
   );

   const [currentMonth, setCurrentMonth] = useState(moment());

   // ГЛАВНОЕ: Смешиваем уроки и платежи
   const studentHistory = useMemo(() => {
      // 1. Считаем общую сумму всех оплат
      const totalPaidSum = (student.payments || []).reduce(
         (sum, p) => sum + p.amount,
         0
      );

      // 2. Обрабатываем уроки
      const lessons = [...allLessons]
         .filter((l) => String(l.student_id) === String(student.id))
         .sort((a, b) => a.lesson_date.localeCompare(b.lesson_date))
         .map((l, index) => {
            const price = student.lesson_price;

            // Считаем, сколько денег потребуют все уроки ОТ начала ДО текущего (включительно)
            const cumulativeCost = (index + 1) * price;

            // Урок оплачен, если общая сумма оплат покрывает его стоимость в очереди
            const isPaid = totalPaidSum >= cumulativeCost;

            return {
               ...l,
               type: 'lesson',
               date: l.lesson_date,
               is_conducted: l.lesson_date <= todayStr,
               is_paid: isPaid,
            };
         });

      // 3. Платежи
      const payments = (student.payments || []).map((p) => ({
         id: p.id,
         date: p.payment_date || p.date,
         type: 'payment',
         amount: p.amount,
      }));

      return [...lessons, ...payments].filter((event) => event.date);
   }, [allLessons, student, todayStr]); // Не забудь добавить todayStr в зависимости
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
               <button onClick={onClose}>
                  <X />
               </button>
            </header>

            <div className="modal-body">
               <StudentCalendar
                  attendedDays={studentHistory}
                  viewDate={currentMonth}
                  setViewDate={setCurrentMonth}
               />
               <PaymentBlock
                  student={student}
                  studentHistory={studentHistory}
               />
               <ProgressBlock student={student} />
            </div>
         </motion.div>
      </div>
   );
};
