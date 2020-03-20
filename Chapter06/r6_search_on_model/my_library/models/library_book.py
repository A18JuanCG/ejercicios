# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)

class LibraryLoan(models.Model):
    _name = 'library.loan'
    _rec_name = 'book_id'
    _order = 'date_end desc'

    member_id = fields.Many2one('library.member', required = True)
    book_id = fields.Many2one('library.book', required = True)
    date_start = fields.Date('Fecha de inicio', default = lambda *a:datetime.now().strftime('%Y-%m-%d'))
    date_end = fields.Date('Fecha de fin', default = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'))
    member_image = fields.Binary('Member image', related = 'member_id.partner_id.image')

    @api.constrains('book_id')
    def check_lent(self):
         for book in self:
            domain = ['&',('book_id.id', '=', book.id), ('date_end', '>=', datetime.now())]
            if self.env['library.loan'].search(domain, count=True) > 1:
                raise UserError('Book is lent!')

    @api.constrains('date_start')
    def chek_date(self):
        if date_start >= date_end:
            raise UserError('Start date after end date!')

class LibraryBook(models.Model):
    _name = 'library.book'
    _description = 'Library Book'

    name = fields.Char('Title', required=True)
    date_release = fields.Date('Release Date')
    date_updated = fields.Datetime('Last Updated', copy=False)
    author_ids = fields.Many2many('res.partner', string='Authors')
    category_id = fields.Many2one('library.book.category', string='Category')
    state = fields.Selection([
        ('draft', 'Unavailable'),
        ('available', 'Available'),
        ('borrowed', 'Borrowed'),
        ('lost', 'Lost')],
        'State', default="draft")
    is_lent = fields.Boolean('Is lent?')
    book_image = fields.Binary('Portada')
    loan_ids = fields.One2many('library.loan', inverse_name = 'book_id')

    @api.multi
    def check_lent(self):
        for book in self:
            domain = ['&',('book_id.id', '=', book.id), ('date_end', '>=', datetime.now())]
            book.is_lent = self.env['library.loan'].search(domain, count=True) > 0

    @api.model
    def is_allowed_transition(self, old_state, new_state):
        allowed = [('draft', 'available'),
                   ('available', 'borrowed'),
                   ('borrowed', 'available'),
                   ('available', 'lost'),
                   ('borrowed', 'lost'),
                   ('lost', 'available')]
        return (old_state, new_state) in allowed

    @api.multi
    def change_state(self, new_state):
        for book in self:
            if book.is_allowed_transition(book.state, new_state):
                book.state = new_state
            else:
                message = _('Pasar de %s a %s no está permitido') % (book.state, new_state)
                raise UserError(message)

    def make_available(self):
        self.change_state('available')

    def make_borrowed(self):
        self.change_state('borrowed')

    def make_lost(self):
        self.change_state('lost')

    def create_categories(self):
        categ1 = {
            'name': 'Child category 1',
            'description': 'Description for child 1'
        }
        categ2 = {
            'name': 'Child category 2',
            'description': 'Description for child 2'
        }
        parent_category_val = {
            'name': 'Parent category',
            'email': 'Description for parent category',
            'child_ids': [
                (0, 0, categ1),
                (0, 0, categ2),
            ]
        }
        # Total 3 records (1 parent and 2 child) will be craeted in library.book.category model
        record = self.env['library.book.category'].create(parent_category_val)
        return True

    @api.multi
    def change_update_date(self):
        self.ensure_one()
        self.date_updated = fields.Datetime.now()

    @api.multi
    def find_book(self):
        domain = [
            '|',
                '&', ('name', 'ilike', 'Book Name'),
                     ('category_id.name', '=', 'Category Name'),
                '&', ('name', 'ilike', 'Book Name 2'),
                     ('category_id.name', '=', 'Category Name 2')
        ]
        books = self.search(domain)
        logger.info('Books found: %s', books)
        return True

    @api.model
    def get_all_library_members(self):
        library_member_model = self.env['library.member']  # This is an empty recordset of model library.member
        return library_member_model.search([])



class LibraryMember(models.Model):
    _name = 'library.member'
    _inherits = {'res.partner': 'partner_id'}

    partner_id = fields.Many2one('res.partner', ondelete='cascade')
    date_start = fields.Date('Member Since')
    date_end = fields.Date('Termination Date')
    member_number = fields.Char()
    date_of_birth = fields.Date('Date of birth')
