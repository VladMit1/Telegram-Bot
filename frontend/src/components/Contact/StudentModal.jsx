import { motion } from 'framer-motion';
import { X, GraduationCap } from 'lucide-react';
import { StudentCalendar } from './components/StudentCalendar';
import { ProgressBlock } from './components/ProgressBlock';

export const StudentModal = ({ student, onClose }) => {
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
               <StudentCalendar attendedDays={student.attended_days || []} />

               <ProgressBlock student={student} />

               <div className="stats-row">
                  <div className="stat-box">
                     <span className="num">{student.total_lessons || 0}</span>
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
