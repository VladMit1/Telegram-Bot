import moment from 'moment';
import { motion, AnimatePresence } from 'framer-motion';

import { Check, PlusCircle, Settings, ChevronDown } from 'lucide-react';
import {
   useCreatePaymentMutation,
   useDeletePaymentMutation,
   useUpdateProgressMutation,
} from '../../../store/apiSlice';
import { useState } from 'react';

export const PaymentBlock = ({ student, studentHistory }) => {
   console.log('🚀 ~ PaymentBlock ~ studentHistory:', student);
   const [updateContact] = useUpdateProgressMutation();
   const [createPayment] = useCreatePaymentMutation();
   const [deletePayment] = useDeletePaymentMutation();

   const [showHistory, setShowHistory] = useState(false);
   const [isPayMode, setIsPayMode] = useState(false);
   const [payAmount, setPayAmount] = useState(500);
   const [payDate, setPayDate] = useState(moment().format('YYYY-MM-DD'));
   const currentBalance =
      student.total_paid -
      studentHistory.filter((h) => h.type === 'lesson').length *
         student.lesson_price;
   const lessonsLeft = Math.floor(currentBalance / student.lesson_price);
   const handleConfirmPayment = async () => {
      try {
         await createPayment({
            student_id: student.id,
            amount: Number(payAmount),
            date: payDate,
         }).unwrap();
         setIsPayMode(false);
      } catch (e) {
         alert('Ошибка при оплате');
      }
   };
   // Функция удаления
   const handleDeletePayment = async (p) => {
      if (window.confirm(`Удалить платеж на ${p.amount} PLN от ${p.date}?`)) {
         await deletePayment({
            paymentId: p.id,
            studentId: student.id,
            amount: p.amount,
         });
      }
   };
   const toggleHistory = () => setShowHistory((prev) => !prev);
   return (
      <div className="payment-block">
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
               <span className="num">{lessonsLeft > 0 ? lessonsLeft : 0}</span>
               <span className="txt">Запас уроков</span>
            </div>
            <div className="stat-box">
               <span className="num">{student.attended_lessons?.length}</span>
               <span className="txt">Посещенные уроки</span>
            </div>
         </div>

         <AnimatePresence mode="wait">
            {isPayMode ? (
               <motion.div
                  className="payment-form-container"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
               >
                  <div className="payment-form-inputs">
                     <div className="input-group">
                        <label>Сумма</label>
                        <input
                           type="number"
                           value={payAmount}
                           onChange={(e) => setPayAmount(e.target.value)}
                        />
                     </div>
                     <div className="input-group">
                        <label>Дата</label>
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
                        <Check size={16} /> Оплатить
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
                     onClick={async () => {
                        const p = prompt('Цена:', student.lesson_price);
                        if (p)
                           await updateContact({
                              id: student.id,
                              lesson_price: Number(p),
                           });
                     }}
                  >
                     <Settings size={18} /> {student.lesson_price} PLN
                  </button>
               </div>
            )}
         </AnimatePresence>
         <div className="payments-history-section">
            <button
               className={`history-toggle ${showHistory ? 'active' : ''}`}
               onClick={toggleHistory}
            >
               <span>История оплат ({student.payments?.length || 0})</span>
               <ChevronDown size={18} className="chevron" />
            </button>

            <AnimatePresence>
               {showHistory && (
                  <motion.div
                     className="history-content"
                     initial={{ height: 0, opacity: 0 }}
                     animate={{ height: 'auto', opacity: 1 }}
                     exit={{ height: 0, opacity: 0 }}
                  >
                     <div className="history-list">
                        {student.payments
                           ?.slice()
                           .reverse()
                           .map((p) => (
                              <div key={p.id} className="payment-row">
                                 <span className="p-date">
                                    {moment(p.payment_date).format('DD.MM.YY')}
                                 </span>
                                 <span className="p-amount">
                                    {p.amount} PLN
                                 </span>
                                 <button onClick={() => handleDeletePayment(p)}>
                                    ✕
                                 </button>
                              </div>
                           ))}
                     </div>
                  </motion.div>
               )}
            </AnimatePresence>
         </div>
      </div>
   );
};
