import { motion } from 'framer-motion';
import { X, GraduationCap } from 'lucide-react';
import { StudentCalendar } from './components/StudentCalendar';
import { ProgressBlock } from './components/ProgressBlock';
import { useMemo } from 'react';
import { useGetLessonsQuery } from '../../store/apiSlice';

export const StudentModal = ({ student, onClose }) => {
   // 1. Получаем все уроки
   const { data: allLessons = [] } = useGetLessonsQuery();

   // 2. Формируем массив объектов дат именно для этого ученика
   const studentHistory = useMemo(() => {
      return allLessons
         .filter((lesson) => String(lesson.student_id) === String(student.id))
         .map((lesson) => ({
            date: lesson.lesson_date, // формат 'YYYY-MM-DD'
            topic: lesson.topic,
            id: lesson.id,
         }));
   }, [allLessons, student.id]);
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
               <StudentCalendar attendedDays={studentHistory || []} />

               <ProgressBlock student={student} />

               <div className="stats-row">
                  <div className="stat-box">
                     <span className="num">{studentHistory.length || 0}</span>
                     <span className="txt">Уроков</span>
                  </div>
                  <div className="stat-box">
                     <span className="num">{student.balance || 0}</span>
                     <span className="txt">Баланс</span>
                  </div>
               </div>
            </div>
         </motion.div>
      </div>
   );
};
